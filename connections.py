from flask import Flask, request, jsonify, make_response
import mysql.connector as sql
import configparser
import sys
import os


def connect():
    global cnx, cursor  # allows us to change variables in the global scope
    try:
        cfile = configparser.ConfigParser()  # reads credentials from the config.ini file (git ignored)
        cfile.read(os.path.join(sys.path[0], "config.ini"))
        # if you are running it in a local development environment, remove "api/"

        cnx = sql.connect(host=cfile["DATABASE"]["DB_HOST"],
                          user=cfile["DATABASE"]["DB_USER"],
                          password=cfile["DATABASE"]["DB_PASS"],
                          database=cfile["DATABASE"]["DB_NAME"])
    except sql.Error as err:
        if err.errno == sql.errorcode.ER_ACCESS_DENIED_ERROR:
            print("User authorization error")
        elif err.errno == sql.errorcode.ER_BAD_DB_ERROR:
            print("Database doesn't exist")
        raise err
    cursor = cnx.cursor()
    return cnx, cursor


def verify_connection():  # reconnects to the database if the connection has been lost
    try:  # tests the connection
        _ = cnx.cursor()  # meaningless statement to test the connection
    except sql.Error:  # if it is not working, it will reconnect
        connect()

cnx, cursor = connect()