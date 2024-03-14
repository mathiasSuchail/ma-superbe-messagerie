from pathlib import Path

from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)



#BDD Sqlite3
import sqlite3
from flask import g

DATABASE = './db/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


#Authentification
app.secret_key = 'cle_secrete'


#ROUTING
@app.route("/")
def index():
    if session.get("loggedUser") is not None:
        return redirect("/mailbox")
    return render_template("dashboard.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("loggedUser") is not None:
            return redirect("/mailbox")
        return render_template("auth/register.html")
    else:
        loggedUser = get_db().execute("SELECT * FROM user WHERE username = ? AND password = ?", (request.form["username"], request.form["password"])).fetchone()
        if loggedUser is None:
            return flash("Utilisateur déjà existant")
        else:
            session["loggedUser"] = loggedUser
            return redirect("/mailbox")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("loggedUser") is not None:
            return redirect("/mailbox")
        return render_template("auth/login.html")
    else:
        loggedUser = get_db().execute("SELECT * FROM user WHERE username = ? AND password = ?", (request.form["username"], request.form["password"])).fetchone()
        if loggedUser is None:
            flash("Identifiants incorrects")
            return redirect("/login")
        else:
            session["loggedUser"] = loggedUser
            return redirect("/mailbox")

@app.route("/logout")
def logout():
    session.pop("loggedUser", None)
    return redirect("/")

@app.route("/mailbox")
def messages():
    if session.get("loggedUser") is None:
        return redirect("/login")
    else:
        return render_template("mailbox.html")

if not Path(DATABASE) .exists():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route("/test")
def test():
    print(query_db('select * from user'))
    return "test"