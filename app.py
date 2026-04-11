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
        "CREATE TABLE Goals (id INTEGER PRIMARY KEY AUTOINCREMENT, exam_name VARCHAR(255) NOT NULL, exam_subject VARCHAR(255) NOT NULL, exam_date VARCHAR(255) NOT NULL, hours_willing REAL NOT NULL, themes TEXT NOT NULL, progress REAL DEFAULT 0.0 CHECK(progress >= 0.0 AND progress <= 100.0), completed BOOLEAN DEFAULT 0, user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES Users(id))"
    )
    db.execute(
        "CREATE TABLE Quests (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) NOT NULL, theme VARCHAR(255) NOT NULL, study_time REAL NOT NULL, time_spent REAL DEFAULT 0.0, date VARCHAR(255) NOT NULL, xp_reward INTEGER DEFAULT 0, stat_points TEXT, description TEXT DEFAULT '', progress REAL DEFAULT 0.0 CHECK(progress >= 0.0 AND progress <= 100.0), completed BOOLEAN DEFAULT 0, failed BOOLEAN DEFAULT 0, goal_id INTEGER NOT NULL, user_id INTEGER NOT NULL, FOREIGN KEY (goal_id) REFERENCES Goals(id), FOREIGN KEY (user_id) REFERENCES Users(id))"
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

@app.route('/goals')
def goals():
    """Display all goals with brief descriptions."""
    db = get_db()
    user_id = current_user.user_id
    rows = db.execute("SELECT * FROM Goals WHERE user_id = ?", [user_id]).fetchall()
    goals = [Goal(
        exam_name=r[1], exam_subject=r[2], exam_date=r[3],
        hours_willing=r[4], themes=r[5].split(',')
    ) for r in rows]
    return render_template('goals.html', goals=goals)


@app.route('/quests')
def quests():
    """Display quests board from mock data."""
    goals = convert_mock_data_to_objects(MOCK_GOALS)
    # Enumerate goals and pass goal_id for each quest link
    goals_with_ids = [(i, goal) for i, goal in enumerate(goals)]
    return render_template('quests.html', goals=goals_with_ids, goal_id=None)


@app.route('/quests/<int:goal_id>')
def quest_detail(goal_id):
    """Display quests for a specific goal."""
    goals = convert_mock_data_to_objects(MOCK_GOALS)
    if goal_id < 0 or goal_id >= len(goals):
        return render_template('quests.html', goals=[]), 404
    # Pass only the selected goal
    return render_template('quests.html', goals=[goals[goal_id]], goal_id=goal_id)


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.route('/study/<int:goal_id>/<int:quest_idx>')
def study(goal_id, quest_idx):
    """Study session page for a specific quest."""
    # Reload or retrieve cached goals
    if 'goals' not in _session_goals:
        _session_goals['goals'] = convert_mock_data_to_objects(MOCK_GOALS)
    
    goals = _session_goals['goals']
    
    if goal_id < 0 or goal_id >= len(goals):
        return render_template('404.html'), 404
    
    goal = goals[goal_id]
    
    if quest_idx < 0 or quest_idx >= len(goal.quests):
        return render_template('404.html'), 404
    
    quest = goal.quests[quest_idx]
    
    # Convert study_time (hours) to seconds for the timer
    timer_seconds = int(quest.study_time * 3600)
    
    return render_template('study.html', goal=goal, quest=quest, goal_id=goal_id, quest_idx=quest_idx, timer_seconds=timer_seconds)


@app.route('/api/study/<int:goal_id>/<int:quest_idx>', methods=['POST'])
def save_study_time(goal_id, quest_idx):
    """Save time spent studying."""
    if 'goals' not in _session_goals:
        return jsonify({'success': False, 'message': 'No study session'}), 400
    
    goals = _session_goals['goals']
    
    if goal_id < 0 or goal_id >= len(goals) or quest_idx < 0 or quest_idx >= len(goals[goal_id].quests):
        return jsonify({'success': False, 'message': 'Invalid goal or quest'}), 400
    
    try:
        data = request.get_json()
        time_spent = float(data.get('time_spent', 0))
        
        if time_spent < 0:
            return jsonify({'success': False, 'message': 'Invalid time'}), 400
        
        quest = goals[goal_id].quests[quest_idx]
        quest.update_time_spent(time_spent)
        
        # Recalc goal progress
        goals[goal_id].recalc_progress()
        
        return jsonify({'success': True, 'message': f'Saved {time_spent:.2f} hours', 'progress': quest.progress})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 400


@app.route('/api/quiz/<int:goal_id>/<int:quest_idx>/<result>', methods=['POST'])
def quiz_result(goal_id, quest_idx, result):
    """Handle quiz pass/fail result."""
    if 'goals' not in _session_goals:
        return {'success': False, 'message': 'No study session'}, 400
    
    goals = _session_goals['goals']
    
    if goal_id < 0 or goal_id >= len(goals) or quest_idx < 0 or quest_idx >= len(goals[goal_id].quests):
        return {'success': False, 'message': 'Invalid goal or quest'}, 400
    
    quest = goals[goal_id].quests[quest_idx]
    
    if result == 'pass':
        quest.completed = True
        quest.failed = False
        # Points would be awarded here
        message = f"Quest passed! You earned {quest.xp_reward} XP"
    elif result == 'fail':
        quest.failed = True
        quest.completed = False
        message = "Quiz failed. Try again later."
    else:
        return {'success': False, 'message': 'Invalid result'}, 400
    
    # Recalc goal progress
    goals[goal_id].recalc_progress()
    
    return {'success': True, 'message': message, 'quest_completed': quest.completed, 'quest_failed': quest.failed}


if __name__ == '__main__':
    app.run(debug=True)