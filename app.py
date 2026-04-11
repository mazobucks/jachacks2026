import os
import sqlite3
import secrets
from flask import Flask, render_template, g

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

path = "study.db"
database_exists = os.path.isfile(path)
db = sqlite3.connect(path)
if not database_exists:
    db.execute(
        "CREATE TABLE Users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255), grade VARCHAR(255))"
    )
    db.execute(
        "CREATE TABLE Stats (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(255), points INTEGER NOT NULL CHECK(points >= 0 AND points <= 100), user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES Users(id))"
    )
    db.commit()

def get_db():
    db = g.get("_database")
    if not db:
        db = sqlite3.connect(path)
        g._database = db
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = g.get("_database")
    if db is not None:
        db.close()

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)

