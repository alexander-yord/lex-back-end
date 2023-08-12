from connections import verify_connection, cursor
from helpers import username_is_unique
from flask import request, jsonify, make_response


def unique():
    """Endpoint that checks whether the username is unique
    """
    verify_connection()  # reconnects to the DB if the connection has been lost
    return make_response(jsonify({"unique": username_is_unique(request.args.get("username").lower())}), 200)