from flask import Flask, request, jsonify, make_response
import mysql.connector as sql
import configparser
import sys
import os

"""Contents:
definition of connect()
definition of the renew_connection decorator
definition of usernameIsUnique()

initialization of the db connection and the Flask app

signup endpoint
uniqueness endpoint
login endpoint
"""


# function to connect to the database
def connect():
    global cnx, cursor  # allows us to change variables in the global scope
    try:
        cfile = configparser.ConfigParser()  # reads credentials from the config.ini file (git ignored)
        cfile.read(os.path.join(sys.path[0], "api/config.ini"))
        # if you are running it in development environment, remove "api/"

        cnx = sql.connect(host=cfile["DATABASE"]["DB_HOST"],
                          user=cfile["DATABASE"]["DB_USER"],
                          password=cfile["DATABASE"]["DB_PASS"],
                          database=cfile["DATABASE"]["DB_NAME"])
    except sql.Error as err:
        if err.errno == sql.errorcode.ER_ACCESS_DENIED_ERROR:
            print("User authorization error")
        elif err.errno == sql.errorcode.ER_BAD_DB_ERROR:
            print("Database doesn't exist")
        raise err
    cursor = cnx.cursor()


def renew_connection(func):
    """Decorator to check if the connection to the database is still active
    and renew it if not
    """
    def wrapper(*args, **kwargs):
        try:
            _ = cnx.cursor()  # meaningless statement to test the connection
        except sql.Error:
            connect()
        func(*args, **kwargs)
    return wrapper()


def usernameIsUnique(username):
    stmt = "SELECT account_id FROM accounts WHERE username = %s"
    usr_tuple = (username,)
    cursor.execute(stmt, usr_tuple)
    _ = cursor.fetchall()
    return True if cursor.rowcount == 0 else False


# database connection variable
cnx = None
connect()  # tries to connect to the database

app = Flask(__name__)


@renew_connection
@app.route("/signup", methods=["POST"])
def signup():
    """Expects a POST request with the
    first_name, last_name, username, password, (email_address (opt), birthday (opt))
    If account successfully created, returns success code 200 and json with
    {success = True, account_id, first_name, last_name, username}, so the user can be automatically
    logged in.
    If not, returns {success = False}
    """
    # gets the values from the POST request
    first_name = request.json.get("first_name")
    last_name = request.json.get("last_name")
    username = request.json.get("username")
    password = request.json.get("password")

    # checks whether the username is unique
    if usernameIsUnique(username):
        # prepares and executes the sql stmt for the accounts table
        stmt = "INSERT INTO accounts (username, first_name, last_name, status) " \
               "VALUES (%s, %s, %s, 'C')"
        account_values = (username, first_name, last_name)
        cursor.execute(stmt, account_values)
        cnx.commit()

        # obtains the account_id of the newly created record as well as the other info needed
        # for the response string
        stmt = "SELECT account_id, username, first_name, last_name " \
               "FROM accounts WHERE username = %s"
        usr_tuple = (username,)
        cursor.execute(stmt, usr_tuple)
        row = cursor.fetchall()[0]

        # prepares and executes the sql stmt for the login_credentials table
        stmt = "INSERT INTO login_credentials (account_id, password) " \
               "VALUES ((SELECT account_id FROM accounts WHERE username = %s), %s)"
        login_values = (row[1], password)
        cursor.execute(stmt, login_values)
        cnx.commit()

        # result dictionary
        result = {
            "success": True,
            "account_id": int(row[0]),
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3]
        }
        return make_response(jsonify(result), 200)
    else:
        return make_response(jsonify({"success": False}))


@renew_connection
@app.route("/uniqueness", methods=["POST"])
def uniqueness():
    """Endpoint that checks whether the username is unique
    """
    return make_response(jsonify({"unique": usernameIsUnique(request.json.get("username"))}))


@renew_connection
@app.route("/login", methods=["POST"])
def login():
    """Endpoint that checks login credentials and if login is successful, returns
    {success = True, account_id, first_name, last_name, username}.
    If not, {success = False, error_no} where
    error_no = 1: username does not exist
    error_no = 2: password is incorrect
    """

    # gets the username and password
    username = request.json.get("username")
    password = request.json.get("password")

    # checks if the username exists
    if not usernameIsUnique(username): # returns False if it exists
        stmt = "SELECT a.account_id, a.username, a.first_name, a.last_name, l.password " \
               "FROM accounts a LEFT JOIN login_credentials l ON a.account_id = l.account_id " \
               "WHERE a.username = %s"
        usrn_tuple = (username, )
        cursor.execute(stmt, usrn_tuple)
        row = cursor.fetchall()[0]

        # checks if passwords match
        if password == row[4]:
            result = {
                "success": True,
                "account_id": int(row[0]),
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3]
            }
            return make_response(jsonify(result), 200)
        else:
            # error_no 2 -- wrong password
            return make_response(jsonify({"success": False, "error_no": 2}))
    else:
        # error_no 1 -- wrong username
        return make_response(jsonify({"success": False, "error_no": 1}))


@app.route("/")
def index():
    return "Welcome to the home page"


if __name__ == '__main__':
    app.run()

