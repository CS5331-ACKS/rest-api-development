#!/usr/bin/python

from flask import Flask, request, g
from flask_cors import CORS
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

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Need to call init_db to load schema if database file was not found
        # Note: connect() automatically creates file if not exists
        init_flag = not os.path.isfile(DATABASE)

        # Set isolation_level=None for autocommit after each API call processed
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None)

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
        'error': 'Missing required parameter(s)',
        'status': False
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
        try:
            cursor = get_db().execute(
            'SELECT fullname FROM users WHERE username=? AND password=?',
            [username, password])
            if len(cursor.fetchall()) == 1:
                print("User successfully authenticated")
                # Generate new UUIDv4 token
                token = str(uuid.uuid4())
                try:
                    get_db().execute(
                    'INSERT INTO tokens VALUES (?, ?, ?)',
                    [username, token, False])
                    print("Inserted token (%s, %s, %s)" %
                    (username, token, False))
                    # Authentication successful response
                    data = {
                        'status': True,
                        'token': token
                    }
                    return make_json_response(data)
                except sqlite3.Error as e:
                    print("sqlite3 error: %s" % e)
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

        # Authentication failed response
        return make_json_response({'status': False})

@app.route("/users/expire", methods=["POST"])
def users_expire():
    if request.method == 'POST':
        print(request.method)
        post_data = request.get_json() or {}
        token = post_data.get('token')

        # All parameters are required
        if None in [token]:
            return respond_missing_params()
        else:
            # Validate UUIDv4 token
            try:
                uuid.UUID(str(token), version=4)
            except ValueError as e:
                print('Invalid UUIDv4 token')
                return make_json_response({'status': False})

        # Expire the token
        try:
            cursor = get_db().execute(
            "UPDATE tokens SET expired=1 WHERE token=? AND expired=0", [token])
            if cursor.rowcount == 0:
                # Token did not exist in database or was already expired
                return make_json_response({'status': False})
            else:
                return make_json_response({'status': True})
        except sqlite3.Error as e:
            print("sqlite3 error: %s" % e)

if __name__ == '__main__':
    # Change the working directory to the script directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Run the application
    app.run(debug=False, port=8080, host="0.0.0.0")
