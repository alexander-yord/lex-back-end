from flask import Flask, request, jsonify, make_response
import mysql.connector as sql
import configparser
import sys
import os

"""Contents:
definition of connect()
definition of username_is_unique()

initialization of the db connection and the Flask app

signup endpoint
uniqueness endpoint
login endpoint
new lex endpoint 
all lexes endpoint
account lexes endpoint
new follower endpoint
"""


# function to connect to the database
def connect():
    global cnx, cursor  # allows us to change variables in the global scope
    try:
        cfile = configparser.ConfigParser()  # reads credentials from the config.ini file (git ignored)
        cfile.read(os.path.join(sys.path[0], "api/config.ini"))
        # if you are running it in a local development environment, remove "api/"

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


def username_is_unique(username):
    stmt = "SELECT count(account_id) FROM accounts WHERE username = %s"
    usr_tuple = (username,)
    cursor.execute(stmt, usr_tuple)
    count = cursor.fetchall()[0][0]  # gets the count
    return True if count == 0 else False


# database connection
cnx = None  # database connection variable
connect()  # connects to the database

# Flask app
app = Flask(__name__)


@app.route("/signup", methods=["POST"])
def signup():
    """Expects a POST request with the
    first_name, last_name, username, password, (email_address (opt), birthday (opt))
    If account successfully created, returns success code 200 and json with
    {success = True, account_id, first_name, last_name, username}, so the user can be automatically
    logged in.
    If not, returns {success = False}
    """
    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

    # gets the values from the POST request
    first_name = request.json.get("first_name").title()
    last_name = request.json.get("last_name").title()
    username = request.json.get("username").lower()  # all usernames should be case insensitive
    password = request.json.get("password")

    # checks whether the username is unique
    if username_is_unique(username):
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


@app.route("/uniqueness", methods=["POST"])
def uniqueness():
    """Endpoint that checks whether the username is unique
    """
    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()
    return make_response(jsonify({"unique": username_is_unique(request.json.get("username").lower())}))


@app.route("/login", methods=["POST"])
def login():
    """Endpoint that checks login credentials and if login is successful, returns
    {success = True, account_id, first_name, last_name, username}.
    If not, {success = False, error_no} where
    error_no = 1: username does not exist
    error_no = 2: password is incorrect
    """

    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

    # gets the username and password
    username = request.json.get("username").lower()
    password = request.json.get("password")

    # checks if the username exists
    if not username_is_unique(username):  # returns False if it exists
        stmt = "SELECT a.account_id, a.username, a.first_name, a.last_name, l.password " \
               "FROM accounts a LEFT JOIN login_credentials l ON a.account_id = l.account_id " \
               "WHERE a.username = %s"
        usrn_tuple = (username,)
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


@app.route("/new", methods=["POST"])
def new():
    """Endpoint that expects the account id of a user and the content of a new lex and
    adds it to the database. If successful, returns {success: True}. Otherwise, returns
    {success: False, error_no: 1/2}, where
    error_no = 1: could not save the record successfully
    error_no = 2: account does not exist
    """

    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

    account_id = request.json.get("account_id")
    content = request.json.get("content")
    status = "R" if request.json.get("status") is None else request.json.get("status")

    if status not in ("P", "R", "D"):  # verifies that the only possible values are P, R, D
        status = "R"

    stmt = "SELECT COUNT(account_id) FROM accounts WHERE account_id = %s"
    id_tuple = (account_id,)
    cursor.execute(stmt, id_tuple)
    if bool(cursor.fetchall()[0][0]):  # checks if this account_id exists
        insert_stmt = "INSERT INTO lexes (content, account_id, status) VALUES (%s, %s, %s)"
        lex_values = (content, account_id, status)
        cursor.execute(insert_stmt, lex_values)
        cnx.commit()

        if cursor.rowcount == 1:  # if a record was created, return true
            return make_response(jsonify({"success": True}))
        else:  # else, return false
            return make_response(jsonify({"success": False, "error_no": 1}))
    else:  # if the account id does not exist, return false
        return make_response(jsonify({"success": False, "error_no": 2}))


@app.route("/all_lexes", methods=["POST"])
def all_lexes():
    """Endpoint that returns a list of 10 lexes (ordered by how recently they were published --
    from most recently to most early). It expects one argument, an index of the lexes. So, index = 0
    would represent lexes 0-9, index 1 - 10-19, etc. In general, from index*10 to (index+1)*10-1.
    This is to allow for async load on scroll. The return format is [{uid, content, account_id,
    first_name, last_name, username, publish_dt}]
    """

    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

    index = 0 if request.json.get("index") is None else request.json.get("index")
    stmt = "SELECT l.uid, l.content, l.publish_dt, a.account_id, a.first_name, a.last_name, " \
           "a.username FROM lexes l LEFT JOIN accounts a ON l.account_id = a.account_id " \
           "WHERE l.status = 'P' " \
           "ORDER BY l.publish_dt DESC LIMIT %s"

    cursor.execute(stmt, ((index + 1) * 10 - 1,))  # executes the stmt limited to (index+1)*10-1 results
    res = []
    for row in cursor.fetchall()[(index * 10):((index + 1) * 10 - 1)]:  # from index*10 to (index+1)*10-1
        lex = {
            "uid": row[0],
            "content": row[1],
            "publish_dt": row[2],
            "account_id": row[3],
            "first_name": row[4],
            "last_name": row[5],
            "username": row[6]
        }
        res.append(lex)
    return make_response(jsonify({"success": True, "result": res}))


@app.route("/account_lexes", methods=["POST"])
def account_lexes():
    """Endpoint to return a list of lexes created by a certain account. Expects an account_id
    and returns {"success": True, "result": [{uid, content, account_id, first_name, last_name,
    username, publish_dt}, ...]}. If unsuccessful, returns {"success": False, "error_no": 1/2}
    where error_no = 1: account does not exist"""

    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

    account_id = request.json.get("account_id")
    stmt = "SELECT COUNT(account_id) FROM accounts WHERE account_id = %s"
    id_tuple = (account_id,)
    cursor.execute(stmt, id_tuple)
    if bool(cursor.fetchall()[0][0]):  # checks if this account_id exists
        stmt = "SELECT l.uid, l.content, l.publish_dt, a.account_id, a.first_name, a.last_name, " \
               "a.username FROM lexes l LEFT JOIN accounts a ON l.account_id = a.account_id " \
               "WHERE l.status = 'P' AND l.account_id = %s " \
               "ORDER BY l.publish_dt DESC LIMIT 75"
        cursor.execute(stmt, id_tuple)

        res = []
        for row in cursor.fetchall():
            lex = {
                "uid": row[0],
                "content": row[1],
                "publish_dt": row[2],
                "account_id": row[3],
                "first_name": row[4],
                "last_name": row[5],
                "username": row[6]
            }
            res.append(lex)
        return make_response(jsonify({"success": True, "result": res}))
    else:  # if the account does not exist
        return make_response(jsonify({"success": False, "error_no": 1}))


@app.route("/new_follower", methods=["POST"])
def new_follower():
    """Endpoint that expects an account_id and the id of the account that has been followed.
    If the record has successfully been recorded, returns {"success": True}. Else,
    {"success": False, "error_no": 1/2} where
    error_no = 1: could not save the record successfully
    error_no = 2: current user's account does not exist
    error_no = 3: followed user's account does not exist"""

    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

    follower_id = request.json.get("account_id")
    account_id = request.json.get("followed_account_id")

    stmt = "SELECT COUNT(account_id) FROM accounts WHERE account_id = %s"
    current_id_tuple = (follower_id,)
    cursor.execute(stmt, current_id_tuple)
    if bool(cursor.fetchall()[0][0]):  # checks if this account_id exists
        followed_account_id_tuple = (account_id,)
        cursor.execute(stmt, followed_account_id_tuple)
        if bool(cursor.fetchall()[0][0]):
            stmt = "INSERT INTO followers (account_id, follower_id) VALUES (%s, %s)"
            argument_tuple = (account_id, follower_id)
            cursor.execute(stmt, argument_tuple)
            cnx.commit()
            if cursor.rowcount == 1:  # if a record was created, return true
                return make_response(jsonify({"success": True}))
            else:  # if a record was not created, return false
                return make_response(jsonify({"success": False, "error_no": 1}))
        else:  # if the account of the user the current user is attempting to follow does not exist
            return make_response(jsonify({"success": False, "error_no": 3}))
    else:  # if the account of the current user does not exist
        return make_response(jsonify({"success": False, "error_no": 2}))


@app.route("/")
def index():
    return "Welcome to the home page"


if __name__ == '__main__':
    app.run()
