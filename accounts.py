from connections import verify_connection, cnx, cursor
from flask import request, jsonify, make_response


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
