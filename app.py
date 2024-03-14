from flask import Flask, render_template

app = Flask(__name__)



#BDD Sqlite3
import sqlite3
from flask import g

DATABASE = '/database.db'
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

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('initBdd.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


#ROUTING
@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/register")
def register():
    return render_template("auth/register.html")

@app.route("/login")
def login():
    return render_template("auth/login.html")

@app.route("/messages")
def messages():
    return render_template("messages.html")