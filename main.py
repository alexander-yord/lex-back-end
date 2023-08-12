from flask import Flask, jsonify, make_response
# v1 APIs
from accounts import signup, login, account_info, uniqueness, my_account, update_account
from lex import new, all_lexes
from followers import new_follower

# Flask app
app = Flask(__name__)
# Account related
app.add_url_rule("/uniqueness", view_func=uniqueness, methods=["POST"])
app.add_url_rule("/signup", view_func=signup, methods=["POST"])
app.add_url_rule("/login", view_func=login, methods=["POST"])
app.add_url_rule("/account_info", view_func=account_info, methods=["POST"])
app.add_url_rule("/my-account", view_func=my_account, methods=["POST"])
app.add_url_rule("/update-account", view_func=update_account, methods=["PUT"])
# Lex related
app.add_url_rule("/new", view_func=new, methods=["POST"])
app.add_url_rule("/all_lexes", view_func=all_lexes, methods=["POST"])
# Followers related
app.add_url_rule("/new_follower", view_func=new_follower, methods=["POST"])


@app.route("/")
def index():
    return make_response("<h1>Welcome to the home page!")


if __name__ == '__main__':
    print(app.url_map)
    app.run()
