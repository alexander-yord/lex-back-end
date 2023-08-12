from connections import verify_connection, cnx, cursor
from helpers import username_is_unique, generate_authorization, verify_authorization, account_exists
from flask import request, jsonify, make_response


def account():
    """Methods:
    GET /account - returns info re the account_id
    POST /account - creates a new account and logs it in
    PUT /account - updates an existing account
    DELETE /account - deletes an existing account
    """

    verify_connection()  # reconnects to the DB if the connection has been lost

    if request.method == "GET":  # get account info

        account_id = request.args.get("account_id")
        current_id = request.args.get("current_id") if request.args.get("current_id") is not None else 0

        if not account_exists(account_id):
            return make_response(jsonify({"status": "Account does not exist!"}), 404)
        if not account_exists(current_id):
            return make_response(jsonify({"status": "You are not logged in!"}), 401)
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

    elif request.method == "POST":  # signup
        """Expects a POST request with the
        first_name, last_name, username, password, (email_address (opt), birthday (opt))
        If account is successfully created, returns success code 200 and json with
        {status, account_id, first_name, last_name, username, token}, so the user can be automatically
        logged in.
        If not, returns 409 and {status}
        """

        # gets the values from the POST request
        first_name = request.json.get("first_name").title()
        last_name = request.json.get("last_name").title()
        username = request.json.get("username").lower()  # all usernames should be case-insensitive
        password = request.json.get("password")

        # checks whether the username is unique
        if username_is_unique(username):
            # prepares and executes the sql stmt for the account table
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

            account_id = int(row[0])
            token = generate_authorization()
            stmt = "insert into login_session (account_no, token) values (%s, %s)"
            account_token_tuple = (account_id, token)
            cursor.execute(stmt, account_token_tuple)
            cnx.commit()

            # result dictionary
            result = {
                "status": "You signed up successfully!",
                "account_id": account_id,
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "token": token
            }
            return make_response(jsonify(result), 200)
        else:
            return make_response(jsonify({"status": "This username is already taken 😞"}), 409)

    elif request.method == "PUT":  # update an existing account
        pass

    elif request.method == "DELETE":  # delete an existing account
        pass

    else:
        pass

