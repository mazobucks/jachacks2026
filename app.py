import os
import sqlite3
import secrets
import werkzeug
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from Goal import Goal
from Quests import Quest
from mock_data import MOCK_GOALS

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

login_manager = LoginManager()
login_manager.init_app(app)

def hash_password(name, password):
    return werkzeug.security.generate_password_hash(name + password)

path = "study.db"
database_exists = os.path.isfile(path)
db = sqlite3.connect(path)
if not database_exists:
    db.execute(
        "CREATE TABLE Users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) UNIQUE, grade VARCHAR(255), password VARCHAR(255))"
    )
    db.execute(
        "CREATE TABLE Stats (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(255), points INTEGER NOT NULL CHECK(points >= 0 AND points <= 100), user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES Users(id))"
    )
    db.execute(
        "INSERT INTO Users (name, grade, password) VALUES (?, ?, ?)",
        ("Test", "A", hash_password("Test", "1234")),
    )
    db.commit()
    db.close()

class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = name
        self.user_id = id
        self.name = name
        self.password = password

def get_db():
    db = g.get("_database")
    if not db:
        g._database = sqlite3.connect(path)
        db = g._database
    return db

@login_manager.user_loader
def user_loader(name):
    record = get_db().execute("SELECT id, password, name FROM Users WHERE name = ? LIMIT 1", [name]).fetchone()
    if not record:
        return None
    return User(record[0], record[2], record[1])

@app.teardown_appcontext
def close_connection(exception):
    db = g.get("_database")
    if db is not None:
        db.close()

@app.route("/")
# Store goals in memory for the session
_session_goals = {}


def convert_mock_data_to_objects(mock_goals):
    """Convert MOCK_GOALS dicts into Goal objects with Quest objects.
    
    Each goal dict is converted to a Goal instance, and its quest dicts
    are converted to Quest objects and added to the goal via add_quest().
    """
    goals = []
    for goal_data in mock_goals:
        # Create Goal object from dict
        goal = Goal(
            exam_name=goal_data.get("exam_name", ""),
            exam_subject=goal_data.get("exam_subject", ""),
            exam_date=goal_data.get("exam_date", ""),
            hours_willing=goal_data.get("hours_willing", 0),
            themes=goal_data.get("themes", []),
        )
        
        # Convert each quest dict to Quest object and add to goal
        quest_dicts = goal_data.get("quests", [])
        for quest_dict in quest_dicts:
            quest = Quest(
                name=quest_dict.get("name", ""),
                theme=quest_dict.get("theme", ""),
                study_time=quest_dict.get("study_time", 0),
                date=quest_dict.get("date", ""),
                xp_reward=quest_dict.get("xp_reward", 0),
                stat_points=quest_dict.get("stat_points", {}),
                associated_goal=goal,
                description=quest_dict.get("description", ""),
            )
            # Set quest progress and completed state from mock data
            quest.progress = quest_dict.get("progress", 0.0)
            quest.completed = quest_dict.get("completed", False)
            
            goal.add_quest(quest)
        
        # After all quests are added, recalc_progress() has been called
        # No need to override the calculated progress from the quest completion counts
        goals.append(goal)
    
    return goals


@app.route('/')
def home():
    return render_template("home.html")

@app.route("/login")
def login_form():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    password = request.form["password"]
    record = get_db().execute("SELECT id, password FROM Users WHERE name = ? LIMIT 1", [name]).fetchone()
    if not record or not werkzeug.security.check_password_hash(record[1], name + password):
        flash("Login info invalid!!!")
        return redirect(url_for("login_form"))
    user = User(record[0], name, record[1])
    login_user(user)
    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

