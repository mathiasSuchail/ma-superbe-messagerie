DROP TABLE IF EXISTS user;
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT ,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

DROP TABLE  IF EXISTS conversation;
CREATE TABLE conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT ,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    FOREIGN KEY (user1_id) REFERENCES user(id),
    FOREIGN KEY (user2_id) REFERENCES user(id)
);

DROP TABLE  IF EXISTS message;
CREATE TABLE message (
    id INTEGER PRIMARY KEY AUTOINCREMENT ,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversation(id),
    FOREIGN KEY (sender_id) REFERENCES user(id)
);


INSERT INTO user (username, password) VALUES ('admin', 'admin');

