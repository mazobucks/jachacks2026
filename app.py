import os
import sqlite3
import secrets
import json
import werkzeug
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from Goal import Goal
from Quests import Quest
from forms import GoalForm, QuestForm
from google import genai
from Quiz import Quiz
from google.genai.types import HttpOptions
from QuestGenerator import QuestGenerator
from datetime import datetime

app = Flask(__name__)
app.secret_key = "HELLO-ashvdasuvd"

#TESTING AREA
quest = Quest(
            name="Study Algebra Basics",
            theme="math",
            study_time=2.5,
            date="2026-05-01",
            xp_reward=100,
            stat_points={"intelligence": 5, "discipline": 2},
            associated_goal=None,
            description="Review core algebra concepts including equations and functions."
        )
#test_quiz = Quiz(quest=quest)
#print(test_quiz)


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"))

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

def hash_password(name, password):
    return werkzeug.security.generate_password_hash(name + password)

path = "study.db"
database_exists = os.path.isfile(path)
db = sqlite3.connect(path)
if not database_exists:
    db.execute(
        "CREATE TABLE Users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) UNIQUE, grade VARCHAR(255), password VARCHAR(255), program VARCHAR(255))"
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
        "INSERT INTO Users (name, grade, password, program) VALUES (?, ?, ?, ?)",
        ("Test", "A", hash_password("Test", "1234"), "Computer Science"),
    )
    db.execute(
        "INSERT INTO Goals (exam_name, exam_subject, exam_date, hours_willing, themes, progress, completed, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Linux System Administrator Certification", "Linux Administration", "2026-06-15", 25.0, "Shell & Scripting,Filesystem,Networking,Security,Services", 0.0, 0, 1)
    )
    db.execute(
        "INSERT INTO Quests (name, theme, study_time, time_spent, date, xp_reward, stat_points, description, progress, completed, failed, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Intro to Shell and Navigation", "Shell & Scripting", 3.0, 0.0, "2026-04-20", 30, '{"focus": 1, "speed": 1}', "Basic shell commands, file navigation, wildcards, and man pages.", 100.0, 1, 0, 1, 1)
    )
    db.execute(
        "INSERT INTO Quests (name, theme, study_time, time_spent, date, xp_reward, stat_points, description, progress, completed, failed, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Bash Scripting Fundamentals", "Shell & Scripting", 5.0, 0.0, "2026-04-22", 60, '{"logic": 2, "focus": 1}', "Variables, control flow, functions, and small automation scripts.", 40.0, 0, 0, 1, 1)
    )
    db.execute(
        "INSERT INTO Quests (name, theme, study_time, time_spent, date, xp_reward, stat_points, description, progress, completed, failed, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Filesystem Hierarchy & Permissions", "Filesystem", 4.0, 0.0, "2026-04-25", 50, '{"memory": 1, "focus": 1}', "FHS layout, ownership, chmod, chown, ACLs, and special permissions.", 20.0, 0, 0, 1, 1)
    )
    db.execute(
        "INSERT INTO Quests (name, theme, study_time, time_spent, date, xp_reward, stat_points, description, progress, completed, failed, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Network Configuration Basics", "Networking", 6.0, 0.0, "2026-05-01", 80, '{"networking": 3, "logic": 1}', "IP addressing, routing, DNS basics, systemd-networkd and net-tools.", 0.0, 0, 0, 1, 1)
    )
    db.execute(
        "INSERT INTO Quests (name, theme, study_time, time_spent, date, xp_reward, stat_points, description, progress, completed, failed, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Securing SSH and Services", "Security", 4.0, 0.0, "2026-05-03", 70, '{"security": 3, "focus": 1}', "Harden SSH, keys, sshd_config, firewall basics (ufw/iptables), and service hardening.", 0.0, 0, 0, 1, 1)
    )
    db.execute(
        "INSERT INTO Quests (name, theme, study_time, time_spent, date, xp_reward, stat_points, description, progress, completed, failed, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("System Services and Logging", "Services", 3.0, 0.0, "2026-05-07", 40, '{"ops": 2}', "systemd units, journalctl, service management, timer units.", 0.0, 0, 0, 1, 1)
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
@login_required
def home():
    goals= get_goals_for_user(current_user.user_id)
    return render_template("home.html", goals=goals, now=datetime.now())

@app.route("/login")
def login_form():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    password = request.form["password"]
    record = get_db().execute("SELECT id, password FROM Users WHERE name = ? LIMIT 1", [name]).fetchone()
    print("Record: ",record)
    if not record or not werkzeug.security.check_password_hash(record[1], name + password):
        print("Record: ",record)
        flash("Login info invalid!!!")
        return redirect(url_for("login_form"))
    user = User(record[0], name, record[1])
    login_user(user)
    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_add():
    name = request.form["name"]
    password = request.form["password"]
    grade = request.form["grade"]
    program = request.form["program"]
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents = (
            f"Using the program: {program}. "
            "Give exactly 3 core skill stats for this program. "
            'Return only JSON as {"stats": ["...", "...", "..."]}.'
        )
    )
        
    try:
        skillsDic = json.loads(response.text)
        stats = skillsDic["stats"]
    except json.JSONDecodeError:
        print("Something went wrong with generating your profile")
    
    try:
        cursor = get_db().execute(
            "INSERT INTO Users (name, grade, password, program) VALUES (?, ?, ?, ?)",
            (name, grade, hash_password(name, password), program),
        )
        get_db().execute(
            "INSERT INTO Stats (title, points, user_id) VALUES (?,?,?)",
            ("Languages", 0, cursor.lastrowid)
        )
        get_db().execute(
            "INSERT INTO Stats (title, points, user_id) VALUES (?,?,?)",
            ("Humanities", 0, cursor.lastrowid)
        )
        get_db().execute(
            "INSERT INTO Stats (title, points, user_id) VALUES (?,?,?)",
            ("P.E.", 0, cursor.lastrowid)
        )
        
        get_db().execute(
            "INSERT INTO Stats (title, points, user_id) VALUES (?,?,?)",
            (stats[0], 0, cursor.lastrowid)
        )
        
        get_db().execute(
            "INSERT INTO Stats (title, points, user_id) VALUES (?,?,?)",
            (stats[1], 0, cursor.lastrowid)
        )
        
        get_db().execute(
            "INSERT INTO Stats (title, points, user_id) VALUES (?,?,?)",
            (stats[2], 0, cursor.lastrowid)
        )
        
        get_db().commit()
        get_db().close()
        return redirect(url_for("login"))
    except sqlite3.DatabaseError:
        flash("Sign up has failed!")
        return redirect(url_for("signup"))

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    db = get_db()
    query = """
        SELECT 
            Users.name, 
            Users.program, 
            SUM(Stats.points) as total_points
        FROM Users
        LEFT JOIN Stats ON Users.id = Stats.user_id
        GROUP BY Users.id
        ORDER BY total_points DESC
    """
    
    try:
        cursor = db.execute(query)
        rows = cursor.fetchall()
        
        leaderboard_data = []
        for i, row in enumerate(rows):
            leaderboard_data.append({
                "rank": i + 1,
                "name": row[0],
                "program": row[1],
                "total_points": row[2] if row[2] is not None else 0
            })
            
        return jsonify(leaderboard_data), 200
        
    except Exception as e:
        print(f"Leaderboard Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/goals')
@login_required
def goals():
    """Display all goals with brief descriptions."""
    goals = get_goals_for_user(current_user.user_id)
    return render_template('goals.html', goals=goals)

@app.route('/delete_goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    db = get_db()
    
    # Verify the goal belongs to the current user before deleting
    goal = db.execute("SELECT id FROM Goals WHERE id = ? AND user_id = ?", (goal_id, current_user.user_id)).fetchone()
    
    if goal:
        # Delete associated quests first (if your DB isn't set to CASCADE)
        db.execute("DELETE FROM Quests WHERE goal_id = ? AND user_id = ?", (goal_id, current_user.user_id))
        
        # Delete the goal
        db.execute("DELETE FROM Goals WHERE id = ? AND user_id = ?", (goal_id, current_user.user_id))
        db.commit()
        flash("Goal and associated quests deleted successfully.")
    else:
        flash("Goal not found or unauthorized.")

    return redirect(url_for('goals'))

def get_goals_for_user(user_id, goal_id=None):
    """Fetch goals (and their quests) from the DB for a given user.
    
    If goal_id is provided, returns a list with just that one goal (or empty if not found).
    Otherwise returns all goals for the user.
    Each goal object has its quests already attached.
    """
    db = get_db()

    if goal_id is not None:
        goal_rows = db.execute(
            "SELECT * FROM Goals WHERE id = ? AND user_id = ?", [goal_id, user_id]
        ).fetchall()
    else:
        goal_rows = db.execute(
            "SELECT * FROM Goals WHERE user_id = ?", [user_id]
        ).fetchall()

    goals = []
    for goal_row in goal_rows:
        goal = Goal(
            exam_name=goal_row[1],
            exam_subject=goal_row[2],
            exam_date=goal_row[3],
            hours_willing=goal_row[4],
            themes=goal_row[5].split(','),
        )
        goal.progress = goal_row[6]
        goal.completed = bool(goal_row[7])
        goal.db_id = goal_row[0]

        quest_rows = db.execute(
            "SELECT * FROM Quests WHERE goal_id = ? AND user_id = ?", [goal_row[0], user_id]
        ).fetchall()

        for row in quest_rows:
            quest = Quest(
                name=row[1],
                theme=row[2],
                study_time=row[3],
                date=row[5],
                xp_reward=row[6],
                stat_points=json.loads(row[7]) if row[7] else {},
                associated_goal=goal,
                description=row[8],
            )
            quest.time_spent = row[4]
            quest.progress = row[9]
            quest.completed = bool(row[10])
            quest.failed = bool(row[11])
            quest.db_id = row[0]
            goal.quests.append(quest)  
        goals.append(goal)
    return goals

@app.route('/quests')
@login_required
def quests():
    goals = get_goals_for_user(current_user.user_id)
    return render_template('quests.html', goals=goals, goal_id=None)


@app.route('/goals/<int:goal_id>')
def goal_detail(goal_id):
    """Display quests for a specific goal."""
    goals = get_goals_for_user(current_user.user_id, goal_id)
    if not goals:
        return render_template('quests.html', goals=[]), 404
    # Pass only the selected goal
    return render_template('quests.html', goals=[goals[0]], goal_id=goal_id)


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.route('/plan')
@login_required
def plan():
    return render_template('plan.html')




@app.route('/plan/new-goal', methods=['GET', 'POST'])
@login_required
def new_goal():
    form = GoalForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO Goals (exam_name, exam_subject, exam_date, hours_willing, themes, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (form.exam_name.data, form.exam_subject.data, form.exam_date.data.isoformat(), 
             form.hours_willing.data, form.themes.data, current_user.user_id)
        )
        goal_id = cursor.lastrowid
        db.commit()
        
        result = generate_quests(
            goal_id=goal_id,
            exam_name=form.exam_name.data,
            exam_subject=form.exam_subject.data,
            exam_date=form.exam_date.data.isoformat(),
            hours_willing=form.hours_willing.data,
            themes_str=form.themes.data,
            files = request.files.getlist('study_documents')
        )
        
        if result:
            flash("Goal created with auto-generated quests!")
            return redirect(url_for('goals'))
        else:
            db.execute("DELETE FROM Goals WHERE id = ?", [goal_id])
            db.commit()
            flash("Error generating quests")
            return render_template('new_goal.html', form=form)
    
    return render_template('new_goal.html', form=form)

@app.route('/plan/new-quest-select')
@login_required
def new_quest_select():
    """Step 1: User selects which goal to add a quest to."""
    goals = get_goals_for_user(current_user.user_id)
    return render_template('new_quest_select.html', goals=goals)

@app.route('/plan/new-quest/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def new_quest(goal_id):
    """Step 2: User fills in quest details for the specific goal."""
    db = get_db()
    goal_row = db.execute("SELECT themes FROM Goals WHERE id = ? AND user_id = ?", 
                          [goal_id, current_user.user_id]).fetchone()
    
    if not goal_row:
        return render_template('404.html'), 404

    form = QuestForm()
    # Dynamically populate dropdowns
    form.goal_id.choices = [(goal_id, "Selected Goal")]
    form.theme.choices = [(t.strip(), t.strip()) for t in goal_row[0].split(',')]

    if form.validate_on_submit():
        db.execute(
            "INSERT INTO Quests (name, theme, study_time, date, xp_reward, description, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (form.name.data, form.theme.data, form.study_time.data, form.date.data.isoformat(),
             form.xp_reward.data, form.description.data, goal_id, current_user.user_id)
        )
        db.commit()
        flash("Quest added!")
        return redirect(url_for('goal_detail', goal_id=goal_id))
    
    return render_template('new_quest.html', form=form)

@app.route('/study/<int:goal_id>/<int:quest_id>')
@login_required
def study(goal_id, quest_id):
    """Study session page for a specific quest."""
    # Reload or retrieve cached goals
    goals = get_goals_for_user(current_user.user_id, goal_id)
    
    if not goals:
        return render_template('404.html'), 404
    
    goal = goals[0]
    
    quest = next((q for q in goal.quests if q.db_id == quest_id), None)
    if quest is None:
        return render_template('404.html'), 404
    
    # Convert study_time (hours) to seconds for the timer
    timer_seconds = int(quest.study_time * 3600)
    
    return render_template('study.html', goal=goal, quest=quest, goal_id=goal_id, quest_id=quest_id, timer_seconds=timer_seconds)


@app.route('/study/<int:goal_id>/<int:quest_id>/<result>', methods=['POST'])
@login_required
def quiz_result(goal_id, quest_id, result):
    if result not in ('pass', 'fail'):
        return render_template('404.html'), 404

    # Save time spent
    time_spent_hours = float(request.form.get('time_spent_seconds', 0))
    row = get_db().execute(
        "SELECT study_time FROM Quests WHERE id = ? AND user_id = ?",
        [quest_id, current_user.user_id]
    ).fetchone()
    if not row:
        return render_template('404.html'), 404

    new_progress = min(100.0, (time_spent_hours / row[0]) * 100.0)
    completed = 1 if result == 'pass' else 0
    failed    = 1 if result == 'fail' else 0

    # Update quest
    get_db().execute(
        "UPDATE Quests SET time_spent = ?, progress = ?, completed = ?, failed = ? WHERE id = ? AND user_id = ?",
        [time_spent_hours, new_progress, completed, failed, quest_id, current_user.user_id]
    )

    # Recalc and update goal progress
    quest_rows = get_db().execute(
        "SELECT completed FROM Quests WHERE goal_id = ? AND user_id = ?",
        [goal_id, current_user.user_id]
    ).fetchall()
    total = len(quest_rows)
    done = sum(1 for r in quest_rows if r[0])
    goal_progress = (done / total * 100.0) if total else 0.0

    get_db().execute(
        "UPDATE Goals SET progress = ?, completed = ? WHERE id = ? AND user_id = ?",
        [goal_progress, 1 if goal_progress >= 100.0 else 0, goal_id, current_user.user_id]
    )
    get_db().commit()

    flash(f"Quest {'passed' if result == 'pass' else 'failed'}!")
    return redirect(url_for('goal_detail', goal_id=goal_id))

def generate_quests(goal_id, exam_name, exam_subject, exam_date, hours_willing, themes_str, files):
    """Generate quests and save to database."""
    try:
        db = get_db()
        themes = [t.strip() for t in themes_str.split(',')]
        extracted_texts = []

        for file in files:
            if file and file.filename.endswith('.txt'):
                extracted_texts.append(file.read().decode('utf-8'))
            # Note: For PDFs or Images, I'll need a library like PyMuPDF (fitz) 
        quests = QuestGenerator.generate_quests(
            goal_name=exam_name,
            exam_subject=exam_subject,
            exam_date=exam_date,
            hours_willing=hours_willing,
            themes=themes,
            documents_contents=extracted_texts
        )
        
        for quest in quests:
            db.execute(
                "INSERT INTO Quests (name, theme, study_time, date, xp_reward, stat_points, description, goal_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (quest.name, quest.theme, quest.study_time, quest.date, quest.xp_reward, 
                json.dumps(quest.stat_points) if quest.stat_points else "{}", 
                quest.description, goal_id, current_user.user_id)
            )
        db.commit()
        return quests
    except Exception as e:
        return None

if __name__ == '__main__':
    app.run(debug=True)