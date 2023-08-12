from connections import verify_connection, cnx, cursor
from flask import request, jsonify, make_response


def new():
    """Endpoint that expects the account id of a user and the content of a new lex and
    adds it to the database. If successful, returns {success: True}. Otherwise, returns
    {success: False, error_no: 1/2}, where
    error_no = 1: could not save the record successfully
    error_no = 2: account does not exist
    """

    verify_connection()  # reconnects to the DB if the connection has been lost

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


def all_lexes():
    """Endpoint that returns a list of 10 lexes (ordered by how recently they were published --
    from most recently to most early). It expects one argument, an index of the lexes. So, index = 0
    would represent lexes 0-9, index 1 - 10-19, etc. In general, from index*10 to (index+1)*10-1.
    This is to allow for async load on scroll. The return format is [{uid, content, account_id,
    first_name, last_name, username, publish_dt}]
    """

    verify_connection()  # reconnects to the DB if the connection has been lost

    index = 0 if request.json.get("index") is None else request.json.get("index")
    stmt = "SELECT l.uid, l.content, l.publish_dt, a.account_id, a.first_name, a.last_name, " \
           "a.username FROM lexes l LEFT JOIN accounts a ON l.account_id = a.account_id " \
           "WHERE l.status = 'P' " \
           "ORDER BY l.publish_dt DESC LIMIT %s"

    cursor.execute(stmt, ((index + 1) * 20 - 1,))  # executes the stmt limited to (index+1)*10-1 results
    res = []
    for row in cursor.fetchall()[(index * 20):((index + 1) * 20 - 1)]:  # from index*10 to (index+1)*10-1
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