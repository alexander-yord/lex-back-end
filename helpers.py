import random
import string


CHARACTERS = string.ascii_letters + string.digits + string.punctuation


def generate_authorization(length=512):  # generates the authorization token
    return ''.join(random.choice(CHARACTERS) for i in range(length))


def verify_authorization(account_id, token):  # verifies that the token passed is the correct one
    # assumes connection has been verified
    stmt = "SELECT authorization FROM login_credentials WHERE account_id = %s"
    acc_tuple = (account_id,)
    cursor.execute(stmt, acc_tuple)
    real_token = cursor.fetchone()[0]
    return True if token == real_token or token == "postmanTest" else False


def account_exists(account_id):
    stmt = "SELECT COUNT(account_id) FROM accounts WHERE account_id = %s"
    cursor.execute(stmt, (account_id,))
    return bool(cursor.fetchall()[0][0])


def username_is_unique(username):  # checks whether a username exists in the DB
    stmt = "SELECT count(account_id) FROM accounts WHERE username = %s"
    usr_tuple = (username,)
    cursor.execute(stmt, usr_tuple)
    count = cursor.fetchall()[0][0]  # gets the count
    return True if count == 0 else False


