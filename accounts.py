from connections import verify_connection, cnx, cursor
from helpers import username_is_unique, generate_authorization, verify_authorization, account_exists
from flask import request, jsonify, make_response


def signup():
    """Expects a POST request with the
    first_name, last_name, username, password, (email_address (opt), birthday (opt))
    If account successfully created, returns success code 200 and json with
    {success = True, account_id, first_name, last_name, username}, so the user can be automatically
    logged in.
    If not, returns {success = False}
    """
    verify_connection()  # reconnects to the DB if the connection has been lost

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
        stmt = "INSERT INTO login_credentials (account_id, password, authorization) " \
               "VALUES ((SELECT account_id FROM accounts WHERE username = %s), %s, %s)"
        authorization_token = generate_authorization()
        login_values = (row[1], password, authorization_token)
        cursor.execute(stmt, login_values)
        cnx.commit()

        # result dictionary
        result = {
            "success": True,
            "account_id": int(row[0]),
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "authorization": authorization_token
        }
        return make_response(jsonify(result), 200)
    else:
        return make_response(jsonify({"success": False}))


def uniqueness():
    """Endpoint that checks whether the username is unique
    """
    verify_connection()  # reconnects to the DB if the connection has been lost
    return make_response(jsonify({"unique": username_is_unique(request.json.get("username").lower())}))


def account_info():
    """An endpoint that returns account information. Expects an account_id and a current_id. Returns
    {"success": True,
     "account_info": {account_id, first_name, last_name, username, "following": True/False},
     "lexes": [{lex}, {}...],
     "following": [{account_id, first_name, last_name, username, "following": True/False}],
     "followers": [{account_id, first_name, last_name, username, "following": True/False}]
    }. If unsuccessful, return error_no = 1: account_id does not exist,
    error_no = 2: current_id does not exist
    """
    verify_connection()  # reconnects to the DB if the connection has been lost

    account_id = request.json.get("account_id")
    current_id = request.json.get("current_id")

    stmt = "SELECT COUNT(account_id) FROM accounts WHERE account_id = %s"
    cursor.execute(stmt, (account_id,))
    if not bool(cursor.fetchall()[0][0]):  # if the account does not exist
        return make_response(jsonify({"success": False, "error_no": 1}))
    cursor.execute(stmt, (current_id,))
    if not bool(cursor.fetchall()[0][0]):  # if the current account does not exist
        return make_response(jsonify({"success": False, "error_no": 2}))
    else:
        # account_info
        stmt = "SELECT a.account_id, a.first_name, a.last_name, a.username, " \
               "CASE WHEN (SELECT COUNT(s.uid) FROM followers s WHERE " \
               "s.account_id=a.account_id AND s.follower_id = %s)>=1 " \
               "THEN 1 ELSE 0 END AS current_following FROM accounts a " \
               "WHERE a.account_id = %s"
        cursor.execute(stmt, (current_id, account_id))
        row = cursor.fetchall()[0]
        account_information = {
            "account_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "username": row[3],
            "following": bool(row[4])
        }

        # lexes
        stmt = "SELECT l.uid, l.content, l.publish_dt, a.account_id, a.first_name, a.last_name, " \
               "a.username FROM lexes l LEFT JOIN accounts a ON l.account_id = a.account_id " \
               "WHERE l.status = 'P' AND l.account_id = %s " \
               "ORDER BY l.publish_dt DESC LIMIT 75"
        cursor.execute(stmt, (account_id,))
        lexes = []
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
            lexes.append(lex)

        # following
        stmt = "SELECT f.account_id, a.first_name, a.last_name, a.username, " \
               "CASE WHEN (SELECT COUNT(s.uid) FROM followers s WHERE s.account_id = f.account_id " \
               "AND s.follower_id  = %s)>=1 THEN 1 ELSE 0 END AS current_following " \
               "FROM followers f LEFT JOIN accounts a ON f.account_id = a.account_id " \
               "WHERE f.follower_id = %s"
        cursor.execute(stmt, (current_id, account_id))
        following = []
        for row in cursor.fetchall():
            account = {
                "account_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "username": row[3],
                "current_following": bool(row[4])
            }
            following.append(account)

        # followers
        stmt = "SELECT f.follower_id, a.first_name, a.last_name, a.username, " \
               "CASE WHEN (SELECT COUNT(s.uid) FROM followers s WHERE s.account_id=f.follower_id " \
               "AND s.follower_id = %s)>=1 THEN 1 ELSE 0 END AS current_following " \
               "FROM followers f LEFT JOIN accounts a ON f.follower_id=a.account_id " \
               "WHERE f.account_id = %s"
        cursor.execute(stmt, (current_id, account_id))
        followers = []
        for row in cursor.fetchall():
            account = {
                "account_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "username": row[3],
                "current_following": bool(row[4])
            }
            followers.append(account)

        # final return
        response = {
            "success": True,
            "account_info": account_information,
            "lexes": lexes,
            "following": following,
            "followers": followers
        }
        return make_response(jsonify(response))


def login():
    """Endpoint that checks login credentials and if login is successful, returns
    {success = True, account_id, first_name, last_name, username}.
    If not, {success = False, error_no} where
    error_no = 1: username does not exist
    error_no = 2: password is incorrect
    """

    verify_connection()  # reconnects to the DB if the connection has been lost

    # gets the username and password
    username = request.json.get("username").lower()
    password = request.json.get("password")

    # checks if the username exists
    if not username_is_unique(username):  # returns False if it exists
        stmt = "SELECT a.account_id, a.username, a.first_name, a.last_name, l.password, l.authorization " \
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
                "last_name": row[3],
                "authorization": row[5]
            }
            return make_response(jsonify(result), 200)
        else:
            # error_no 2 -- wrong password
            return make_response(jsonify({"success": False, "error_no": 2}))
    else:
        # error_no 1 -- wrong username
        return make_response(jsonify({"success": False, "error_no": 1}))


def my_account():
    """An endpoint that expects an account_id and an authorization token and returns information about the user's
    account. Format:
    { account_id, first_name, last_name, username, birthday_date, email_address, status, password }
    If something is not right, returns {"success": False, "error_no": 1/2} where
    error_no = 1: account does not exist
    error_no = 2: authorization token is incorrect
    """
    verify_connection()

    account_id = request.json.get("account_id")
    token = request.json.get("authorization")

    if not account_exists(account_id):
        return make_response(jsonify({"success": False, "error_no": 1}), 200)
    if not verify_authorization(account_id, token):
        return make_response(jsonify({"success": False, "error_no": 2}), 200)

    # if account exists and is authorized
    stmt = "SELECT a.first_name, a.last_name, a.username, a.birthday_date, a.email_address, a.status, l.password " \
           "FROM accounts a JOIN login_credentials l ON a.account_id=l.account_id " \
           "WHERE a.account_id = %s"
    cursor.execute(stmt, (account_id,))
    row = cursor.fetchone()

    result = {
        "success": True,
        "account_id": account_id,
        "first_name": row[0],
        "last_name": row[1],
        "username": row[2],
        "birthdate": row[3],
        "email": row[4],
        "status": row[5],
        "password": row[6]
    }
    return make_response(jsonify(result), 200)


def update_account():
    """Endpoint that expect { account_id, authorization, old_username, username, first_name, last_name, birthday_date,
    email_address, password }. If something is not right, returns {"success": False, "error_no": 1/2/3} where
    error_no = 1: account does not exist
    error_no = 2: authorization token is incorrect
    error_no = 3: new username is not unique
    """
    verify_connection()

    # obtaining each of the variables from the JSON request
    account_id = request.json.get('account_id')
    token = request.json.get('authorization')
    first_name = request.json.get('first_name').title()
    last_name = request.json.get('last_name').title()
    old_username = request.json.get('old_username')
    username = request.json.get('username')
    birthday_date = request.json.get('birthday_date')
    email_address = request.json.get('email_address')
    password = request.json.get('password')

    if not account_exists(account_id):
        return make_response(jsonify({"success": False, "error_no": 1}), 200)
    if not verify_authorization(account_id, token):
        return make_response(jsonify({"success": False, "error_no": 2}), 200)
    if old_username != username and not username_is_unique(username):
        return make_response(jsonify({"success": False, "error_no": 3}), 200)

    # else
    stmt_account = "UPDATE accounts " \
                   "SET username = %s, first_name = %s, last_name = %s, birthday_date = %s, email_address = %s " \
                   "WHERE account_id = %s"
    bind = (username, first_name, last_name, birthday_date, email_address, account_id)
    cursor.execute(stmt_account, bind)
    cnx.commit()

    stmt_pass = "UPDATE login_credentials SET password = %s WHERE account_id = %s"
    cursor.execute(stmt_pass, (password, account_id))
    cnx.commit()

    return make_response(jsonify({"success": True}), 200)