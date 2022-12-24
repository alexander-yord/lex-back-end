from flask import Flask
import mysql.connector as sql
import configparser
import sys
import os

cnx = None
try:
    cfile = configparser.ConfigParser()
    cfile.read(os.path.join(sys.path[0], "api/config.ini"))
    # if you are running it in development environment, remove "api/"

    cnx = sql.connect(host=cfile["DATABASE"]["DB_HOST"],
                      user=cfile["DATABASE"]["DB_USER"],
                      password=cfile["DATABASE"]["DB_PASS"],
                      database=cfile["DATABASE"]["DB_NAME"])
except FileNotFoundError as error:
    print("File was not found: ", error)
    raise FileNotFoundError
except sql.Error as err:
    if err.errno == sql.errorcode.ER_ACCESS_DENIED_ERROR:
        print("User authorization error")
    elif err.errno == sql.errorcode.ER_BAD_DB_ERROR:
        print("Database doesn't exist")
    raise err

app = Flask(__name__)


@app.route("/")
def index():
    return "Welcome to the home page"


if __name__ == '__main__':
    app.run()

