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

def make_json_response(data, status=True, code=200):
    """Utility function to create the JSON responses."""

    to_serialize = {}
    if status:
        to_serialize['status'] = True
        if data is not None:
            to_serialize['result'] = data
    else:
        to_serialize['status'] = False
        to_serialize['error'] = data
    response = app.response_class(
        response=json.dumps(to_serialize),
        status=code,
        mimetype='application/json'
    )
    return response

### DATABASE Functionalities ###

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        print("Setting up database connection")
        # Need to call init_db to load schema if database file was not found
        # Note: connect() automatically creates file if not exists
        init_flag = not os.path.isfile(DATABASE)

        # Set isolation_level=None for autocommit after each API call processed
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None)

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

### API Routes ###

@app.route("/")
def index():
    """Returns a list of implemented endpoints."""
    return make_json_response(ENDPOINT_LIST)


@app.route("/meta/heartbeat")
def meta_heartbeat():
    """Returns true"""
    return make_json_response(None)


@app.route("/meta/members")
def meta_members():
    """Returns a list of team members"""
    with open("./team_members.txt") as f:
        team_members = f.read().strip().split("\n")
    return make_json_response(team_members)

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
            data = {'error': 'Missing required parameter(s)'}
            return make_json_response(data)
        else:
            # Perform input validation
            try:
                age = int(age)
            except ValueError:
                data = {'error': 'Age must be a positive integer'}
                return make_json_response(data)

        # Attempts to insert the user into the database
        # Raises IntegrityError if username already exists in database
        try:
            get_db().execute('INSERT INTO users VALUES(?,?,?,?)',
            [username, password, fullname, age])
            print("Inserted user {%s, %s, %s, %d}" %
            (username, password, fullname, age))
        except sqlite3.IntegrityError:
            data = {'error': 'User already exists!'}
            return make_json_response(data)
        return make_json_response(None, code=201)

if __name__ == '__main__':
    # Change the working directory to the script directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Run the application
    app.run(debug=False, port=8080, host="0.0.0.0")
