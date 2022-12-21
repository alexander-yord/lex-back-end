from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Welcome to the home page"


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
