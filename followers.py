from connections import verify_connection, cnx, cursor
from helpers import username_is_unique, generate_authorization
from flask import request, jsonify, make_response


def new_follower():
    """Endpoint that expects an account_id, the id of the account to be followed, and an action
    -- A (add) or D (delete). For action = A (add), if the record has successfully been recorded,
    returns {"success": True}. Else, {"success": False, "error_no": 1/2/3} where
    error_no = 1: could not save the record successfully
    error_no = 2: current user's account does not exist
    error_no = 3: followed user's account does not exist.
    For action = D (delete), if the record was successfully deleted or if it didn't exist, returns
    {"success": True}. """

    verify_connection()  # reconnects to the DB if the connection has been lost

    follower_id = request.json.get("account_id")
    account_id = request.json.get("followed_account_id")
    action = "A" if request.json.get("action") is None else request.json.get("action")
    if action not in ("A", "D"):  # verifies that the action is either Add or Delete
        action = "A"

    stmt = "SELECT COUNT(account_id) FROM account WHERE account_id = %s"
    cursor.execute(stmt, (follower_id,))
    if not bool(cursor.fetchall()[0][0]):
        return make_response(jsonify({"success": False, "error_no": 2}))
    cursor.execute(stmt, (account_id,))
    if not bool(cursor.fetchall()[0][0]):
        return make_response(jsonify({"success": False, "error_no": 3}))

    stmt = "SELECT COUNT(uid) FROM followers WHERE account_id = %s AND follower_id = %s"
    argument_tuple = (account_id, follower_id)
    cursor.execute(stmt, argument_tuple)
    number_of_records = cursor.fetchall()[0][0]

    if action == "A":  # if the action is add
        if bool(number_of_records):  # checks if such record doesn't already exist
            return make_response(jsonify({"success": True, "action": "A"}))
        else:
            stmt = "INSERT INTO followers (account_id, follower_id) VALUES (%s, %s)"
            argument_tuple = (account_id, follower_id)
            cursor.execute(stmt, argument_tuple)
            cnx.commit()
            if cursor.rowcount == 1:  # if a record was created, return true
                return make_response(jsonify({"success": True}))
            else:  # if a record was not created, return false
                return make_response(jsonify({"success": False, "error_no": 1}))
    else:  # if the action is delete
        stmt = "DELETE FROM followers WHERE account_id = %s and follower_id = %s"
        cursor.execute(stmt, (account_id, follower_id))
        cnx.commit()
        if cursor.rowcount == number_of_records:  # if all such records have been deleted
            return make_response(jsonify({"success": True, "action": "D"}))
        else:
            return make_response(jsonify({"success": False, "action": "D"}))
