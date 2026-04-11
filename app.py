from flask import Flask, render_template, redirect, url_for
from Goal import Goal
from Quests import Quest
from mock_data import MOCK_GOALS

app = Flask(__name__)


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
                start=quest_dict.get("start", ""),
                end=quest_dict.get("end", ""),
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
    return render_template('home.html')


@app.route('/goals')
def goals():
    """Display all goals with brief descriptions."""
    goals = convert_mock_data_to_objects(MOCK_GOALS)
    return render_template('goals.html', goals=goals)


@app.route('/quests')
def quests():
    """Display quests board from mock data."""
    goals = convert_mock_data_to_objects(MOCK_GOALS)
    return render_template('quests.html', goals=goals)


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


if __name__ == '__main__':
    app.run(debug=True)

