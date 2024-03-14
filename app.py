from pathlib import Path

from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

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
        userExist = get_db().execute("SELECT id FROM user WHERE username = ?", (request.form["username"],)).fetchone()
        if userExist:
            return redirect(url_for('register', error="Nom d'utilisateur déjà existant."))
        if request.form["password"] != request.form["cpassword"]:
            return redirect(url_for('register', error="Les mots de passe ne correspondent pas."))
        if len(request.form["password"]) < 8:
            return redirect(url_for('register', error="Le mot de passe doit contenir au moins 8 caractères."))
        if len(request.form["username"]) < 4:
            return redirect(url_for('register', error="Le nom d'utilisateur doit contenir au moins 4 caractères."))

        else:
            get_db().execute("INSERT INTO user (username, password) VALUES (?, ?)", (request.form["username"], request.form["password"]))
            get_db().commit()
            return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("loggedUser") is not None:
            return redirect("/mailbox")
        return render_template("auth/login.html")
    else:
        #Récupération de l'utilisateur
        loggedUser = get_db().execute("SELECT * FROM user WHERE username = ? AND password = ?", (request.form["username"], request.form["password"])).fetchone()

        #Récupération des nom des colonnes
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM user LIMIT 1')
        field_names = [i[0] for i in cursor.description]

        if loggedUser is None:
            return redirect(url_for('login', error="Nom d'utilisateur ou mot de passe incorrect."))
        else:
            loggedUser = dict(zip(field_names, loggedUser))
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

if not Path(DATABASE).is_file():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route("/api/conversations")
def conversations():
    #récupération des conversations
    user_id = session["loggedUser"]["id"]
    conversations_data = query_db('SELECT * FROM conversation WHERE user1_id = ? OR user2_id = ?', (user_id, user_id))

    #récupération des noms des colonnes
    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM conversation LIMIT 1')
    field_names = [i[0] for i in cursor.description]
    conversations = [dict(zip(field_names, row)) for row in conversations_data]

    #récupération du nom du déstinataire
    for conversation in conversations:
        if conversation["user1_id"] == user_id:
            conversation["name"] = query_db('SELECT username FROM user WHERE id = ?', (conversation["user2_id"],), True)[0]
        else:
            conversation["name"] = query_db('SELECT username FROM user WHERE id = ?', (conversation["user1_id"],), True)[0]

    #récupération des messages avec les champs de la conversation
    for conversation in conversations:
        messages = query_db('SELECT * FROM message WHERE conversation_id = ?', (conversation["id"],))

        cursor.execute('SELECT * FROM message LIMIT 1')
        field_names = [i[0] for i in cursor.description]
        conversation["messages"] = [dict(zip(field_names, row)) for row in messages]
        for message in conversation["messages"]:
            message["name"] = query_db('SELECT username FROM user WHERE id = ?', (message["sender_id"],), True)[0]


    return jsonify(conversations)

@app.route("/api/user")
def user():
    user = query_db('SELECT id, username FROM user WHERE id = ?', (session["loggedUser"]["id"],), True)
    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM user LIMIT 1')
    field_names = [i[0] for i in cursor.description]
    return jsonify(dict(zip(field_names, user)))

@app.route("/api/messages", methods=["POST"])
def messages_post():
    if session.get("loggedUser") is None:
        return jsonify({"error": "Non connecté"})
    else:
        data = request.get_json()
        conversation_id = data["conversation_id"]
        content = data["content"]
        sender_id = session["loggedUser"]["id"]

        get_db().execute("INSERT INTO message (conversation_id, sender_id, content) VALUES (?, ?, ?)", (conversation_id, sender_id, content))
        get_db().commit()
        return jsonify({"status": "ok"})

#retour tous les utlisateurs à qui je n'ai jamais envoyé de messages
@app.route("/api/new_friends")
def new_friends():
    user_id = session["loggedUser"]["id"]

    conversations = query_db('SELECT user1_id, user2_id FROM conversation WHERE user1_id = ? OR user2_id = ?', (user_id, user_id))
    userIds = []
    for conversation in conversations:
        if conversation[0] != user_id:
            userIds.append(conversation[0])
        else:
            userIds.append(conversation[1])

    friends = query_db('SELECT user.id, user.username FROM user WHERE user.id NOT IN ({}) AND user.id != ?'.format(','.join('?'*len(userIds))), userIds + [user_id])

    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM user LIMIT 1')
    field_names = [i[0] for i in cursor.description]
    return jsonify([dict(zip(field_names, row)) for row in friends])

@app.route("/api/create_conversation", methods=["POST"])
def create_conversation():
    user_id = session["loggedUser"]["id"]
    friend_id = request.get_json()["friend_id"]
    get_db().execute("INSERT INTO conversation (user1_id, user2_id) VALUES (?, ?)", (user_id, friend_id))
    get_db().commit()

    convsersation_id = get_db().execute("SELECT id FROM conversation WHERE user1_id = ? AND user2_id = ?", (user_id, friend_id)).fetchone()[0]
    return jsonify(convsersation_id)

@app.route("/test")
def test():
    print(query_db('select * from user'))
    return "test"