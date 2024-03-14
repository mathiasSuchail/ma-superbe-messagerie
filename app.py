from flask import Flask, render_template

app = Flask(__name__)



#BDD Sqlite3
import sqlite3
from flask import g


import sqlite3
from flask import g

DATABASE = './db/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


#ROUTING
@app.route("/")
def index():
    cur = get_db().cursor()
    return render_template("dashboard.html")

@app.route("/register")
def register():
    return render_template("auth/register.html")

@app.route("/login")
def login():
    return render_template("auth/login.html")

@app.route("/mailbox")
def messages():
    return render_template("mailbox.html")