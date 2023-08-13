from flask import Flask, jsonify, make_response
# v1 APIs
from accounts import signup, login1, account_info, uniqueness, my_account, update_account
from lex import new, all_lexes
from followers import new_follower
# v2 APIs
from account.uniqueness import unique
from account.login import login
from account.account import account

# Flask app
app = Flask(__name__)
# VERSION 1
# Account related
app.add_url_rule("/uniqueness", view_func=uniqueness, methods=["POST"])
app.add_url_rule("/signup", view_func=signup, methods=["POST"])
app.add_url_rule("/login", view_func=login1, methods=["POST"])
app.add_url_rule("/account_info", view_func=account_info, methods=["POST"])
app.add_url_rule("/my-account", view_func=my_account, methods=["POST"])
app.add_url_rule("/update-account", view_func=update_account, methods=["PUT"])
# Lex related
app.add_url_rule("/new", view_func=new, methods=["POST"])
app.add_url_rule("/all_lexes", view_func=all_lexes, methods=["POST"])
# Followers related
app.add_url_rule("/new_follower", view_func=new_follower, methods=["POST"])

# VERSION 2
app.add_url_rule("/v2/account", view_func=account, methods=["POST", "GET"])
app.add_url_rule("/v2/unique", view_func=unique, methods=["GET"])
app.add_url_rule("/v2/login", view_func=login, methods=["POST"])


@app.route("/")
def index():
    return make_response("<h1>Welcome to the home page!</h1>")


if __name__ == '__main__':
    print(app.url_map)
    app.run()
