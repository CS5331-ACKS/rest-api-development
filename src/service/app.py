#!/usr/bin/python

from flask import Flask, request, g
from flask_cors import CORS
import datetime
import json
import os
import sqlite3
import uuid

app = Flask(__name__)
# Enable cross origin sharing for all endpoints
CORS(app)

# Remember to update this list
ENDPOINT_LIST = ['/', '/meta/heartbeat', '/meta/members']

DATABASE = 'database.db'

### DATABASE Functionalities ###

# Adapters to make sqlite3 store boolean as integers and back
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: v != '0')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Need to call init_db to load schema if database file was not found
        # Note: connect() automatically creates file if not exists
        init_flag = not os.path.isfile(DATABASE)

        # Set isolation_level=None for autocommit after each API call processed
        # Set detect_types=sqlite3.PARSE_DECLTYPES to auto convert custom types
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)

        # Set row factory to sqlite3.Row to get associative result sets
        db.row_factory = sqlite3.Row

        if init_flag:
            init_db(db)
    return db

def init_db(db):
    """Initialize Sqlite3 database"""
    with app.app_context():
        with app.open_resource('schema.sql', mode='r') as file:
            db.cursor().executescript(file.read())

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

### Response Helpers ###

def make_json_response(data, status=200):
    """Utility function to create the JSON responses."""
    response = app.response_class(
        response=json.dumps(data),
        status=status,
        mimetype='application/json'
    )
    return response

def respond_missing_params():
    data = {
        "status": False,
        "error": "Missing required parameter(s)",
    }
    return make_json_response(data)

def respond_invalid_token():
    data = {
        "status": False,
        "error": "Invalid authentication token."
    }
    return make_json_response(data)

### API Routes ###

@app.route("/")
def index():
    """Returns a list of implemented endpoints."""
    data = {
        'status': True,
        'result': ENDPOINT_LIST
    }
    return make_json_response(data)


@app.route("/meta/heartbeat")
def meta_heartbeat():
    """Returns true"""
    data = {
        'status': True
    }
    return make_json_response(data)


@app.route("/meta/members")
def meta_members():
    """Returns a list of team members"""
    with open("./team_members.txt") as f:
        team_members = f.read().strip().split("\n")
        data = {
            'status': True,
            'result': team_members
        }
        return make_json_response(data)

@app.route("/users", methods=["POST"])
def users():
    if request.method == "POST":
        post_data = request.get_json() or {}
        token = post_data.get("token")

        # All parameters are required
        if None in [token]:
            return respond_missing_params()

        # Check token validity and if expired
        try:
            cursor = get_db().execute(
            "SELECT username, fullname, age FROM tokens NATURAL JOIN users WHERE token=? AND expired=0", [token])
            row = cursor.fetchone()
            if row is not None:
                data = {
                    "status": True,
                    "username": row["username"],
                    "fullname": row["fullname"],
                    "age": row["age"]
                }
                return make_json_response(data)
            else:
                data = {
                    "status": False,
                    "error": "Invalid authentication token."
                }
                return make_json_response(data)
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

@app.route("/users/register", methods=["POST"])
def users_register():
    if request.method == 'POST':
        post_data = request.get_json() or {}
        username = post_data.get("username")
        password = post_data.get("password")
        fullname = post_data.get("fullname")
        age = post_data.get("age")

        # All parameters are required
        if None in [username, password, fullname, age]:
            return respond_missing_params()
        else:
            # Perform input validation
            try:
                age = int(age)
            except ValueError:
                data = {
                    'status': False,
                    'error': 'Age must be a positive integer'
                }
                return make_json_response(data)

        # Attempts to insert the user into the database
        # Raises IntegrityError if username already exists in database
        try:
            get_db().execute('INSERT INTO users VALUES(?,?,?,?)',
            [username, password, fullname, age])
            print("Inserted user {%s, %s, %s, %d}" %
            (username, password, fullname, age))
        except sqlite3.IntegrityError:
            data = {
                'status': False,
                'error': 'User already exists!'
            }
            return make_json_response(data)

        # User created response
        return make_json_response({'status': True}, status=201)

@app.route("/users/authenticate", methods=["POST"])
def users_authenticate():
    if request.method == 'POST':
        post_data = request.get_json() or {}
        username = post_data.get('username')
        password = post_data.get('password')

        # All parameters are required
        if None in [username, password]:
            return respond_missing_params()

        # Authenticate user
        if authenticate_user(username, password):
            token = generate_token(username)
            if token is not None:
                # Authentication successful response
                data = {
                    "status": True,
                    "token": token
                }
                return make_json_response(data)

        # Assume authentication failed
        return make_json_response({"status": False})

@app.route("/users/expire", methods=["POST"])
def users_expire():
    if request.method == 'POST':
        post_data = request.get_json() or {}
        token = post_data.get('token')

        # All parameters are required
        if None in [token]:
            return respond_missing_params()

        # Validate UUIDv4 token and check if token is not expired
        is_token_valid, username = validate_token(token)
        if not is_token_valid:
            return respond_invalid_token()

        # Expire the token
        try:
            cursor = get_db().execute(
            "UPDATE tokens SET expired = 1 WHERE token = ? AND expired = 0", [token])
            if cursor.rowcount == 0:
                # Token did not exist in database or was already expired
                return make_json_response({'status': False})
            else:
                print("Updated token (%s)" % token)
                return make_json_response({'status': True})
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

@app.route("/diary", methods=["GET", "POST"])
def diary():
    if request.method == "GET":
        # Get public diary entries endpoint (GET /diary)
        try:
            cursor = get_db().execute("SELECT * FROM diary_entries WHERE public = 1")
            rows = [dict(row) for row in cursor.fetchall()]
            data = {
                "status": True,
                "results": rows
            }
            return make_json_response(data)
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)
            return make_json_response({"status": False})
    elif request.method == "POST":
        # Get authenticated user diary entries endpoint (POST /diary)
        post_data = request.get_json() or {}
        token = post_data.get("token")

        # All parameters are required
        if None in [token]:
            return respond_missing_params()

        # Validate UUIDv4 token and check if token is not expired
        is_token_valid, username = validate_token(token)
        if not is_token_valid:
            return respond_invalid_token()

        # Retrieve diary entries belonging to authenticated user
        try:
            cursor = get_db().execute(
            "SELECT * FROM diary_entries WHERE author = ?",
            [username])
            rows = [dict(row) for row in cursor.fetchall()]
            data = {
                "status": True,
                "results": rows
            }
            return make_json_response(data)
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

@app.route("/diary/create", methods=["POST"])
def diary_create():
    if request.method == 'POST':
        post_data = request.get_json() or {}
        token = post_data.get("token")
        title = post_data.get("title")
        public = post_data.get("public")
        text = post_data.get("text")

        # All parameters are required
        if None in [token, title, public, text]:
            return respond_missing_params()
        else:
            # Validate acceptable values for public attribute
            try:
                public = int(public)
                if public not in [0, 1]:
                    raise ValueError("Value of public must be 0 or 1")
            except ValueError as e:
                print("Value of public is not 0 or 1")
                data = {
                    "status": False,
                    "error": "Invalid value for public."
                }
                return make_json_response(data)

        # Validate UUIDv4 token and check if token is not expired
        is_token_valid, username = validate_token(token)
        if not is_token_valid:
            return respond_invalid_token()

        # Create diary entry
        try:
            current_time = datetime.datetime.now().replace(microsecond=0).isoformat()
            public = bool(public == 1)
            cursor = get_db().execute(
            "INSERT INTO diary_entries VALUES(NULL, ?, ?, ?, ?, ?)",
            [title, username, current_time, public, text])
            diary_entry_id = cursor.lastrowid
            print("Inserted diary entry (%d, %s, %s, %s, %s, ...)" %
            (diary_entry_id, title, username, current_time, public))
            data = {
                "status": True,
                "id": diary_entry_id
            }
            return make_json_response(data, status=201)
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

@app.route("/diary/delete", methods=["POST"])
def diary_delete():
    if request.method == 'POST':
        post_data = request.get_json() or {}
        token = post_data.get("token")
        id = post_data.get("id")

        # All parameters are required
        if None in [token, id]:
            return respond_missing_params()

        # Validate UUIDv4 token and check if token is not expired
        is_token_valid, username = validate_token(token)
        if not is_token_valid:
            return respond_invalid_token()

        # Validate diary entry id
        try:
            cursor = "SELECT * FROM diary_entries, tokens,"
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

        # Assume validation failure response
        return make_json_response({"status": False})

### Helper function(s) ###

def authenticate_user(username, password):
    try:
        cursor = get_db().execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        [username, password])
        if len(cursor.fetchall()) == 1:
            print("User successfully authenticated")
            return True
        else:
            return False
    except sqlite3.Error as e:
        print("sqlite3 error: %s" % e)
        return False

def generate_token(username):
    try:
        token = str(uuid.uuid4())
        get_db().execute(
        'INSERT INTO tokens VALUES (?, ?, ?)',
        [username, token, False])
        print("Inserted token (%s, %s, False)" % (username, token))
        return token
    except sqlite3.Error as e:
        print("sqlite3 error: %s" % e)
        return None

def validate_token(token):
    # Validate UUIDv4 token
    try:
        uuid.UUID(str(token), version=4)
    except ValueError as e:
        print("Invalid UUIDv4 token")
        return False, None

    # Check if token has expired
    try:
        cursor = get_db().execute(
        "SELECT * FROM tokens WHERE token = ? AND expired = 0", [token])
        rows = cursor.fetchall()
        if len(rows) == 0:
            print("Invalid or expired token (%s)" % token)
            return False, None
        else:
            print(rows)
            return True, rows[0]["username"]
    except sqlite3.Error as e:
        print("sqlite3 error: %s" % e)
        return False, None

if __name__ == '__main__':
    # Change the working directory to the script directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Run the application
    app.run(debug=False, port=8080, host="0.0.0.0")
