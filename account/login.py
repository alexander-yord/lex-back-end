from connections import verify_connection, cnx, cursor
from helpers import username_is_unique, generate_authorization, verify_authorization, account_exists
from flask import request, jsonify, make_response


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

    if username is None or password is None:
        return make_response({"status": "Please enter both a username and a password"}, 400)

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
            # insert a session token into the db
            account_id = int(row[0])
            token = generate_authorization()
            stmt = "insert into login_session (account_no, token) values (%s, %s)"
            account_token_tuple = (account_id, token)
            cursor.execute(stmt, account_token_tuple)
            cnx.commit()

            result = {
                "status": "You successfully logged in!",
                "account_id": account_id,
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "token": token
            }
            return make_response(jsonify(result), 200)
        else:
            # error_no 2 -- wrong password
            return make_response(jsonify({"status": "Wrong password"}), 401)
    else:
        # error_no 1 -- wrong username
        return make_response(jsonify({"status": "The username could not be found"}), 404)
