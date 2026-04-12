from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, IntegerField, SelectField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired, NumberRange

class GoalForm(FlaskForm):
    exam_name = StringField('Exam Name', validators=[DataRequired()])
    exam_subject = StringField('Subject', validators=[DataRequired()])
    exam_date = DateField('Exam Date', format='%Y-%m-%d', validators=[DataRequired()])
    hours_willing = FloatField('Planned Study Hours', validators=[DataRequired()])
    themes = StringField('Themes (comma-separated)', validators=[DataRequired()])
    
    # Add the files field here
    study_documents = MultipleFileField('Upload Study Materials')

class QuestForm(FlaskForm):
    name = StringField('Quest Name', validators=[DataRequired()])
    goal_id = SelectField('Associated Goal', coerce=int, validators=[DataRequired()])
    theme = SelectField('Theme', choices=[], validators=[DataRequired()])
    study_time = FloatField('Estimated Hours', validators=[DataRequired(), NumberRange(min=0.1)])
    date = DateField('Target Date', format='%Y-%m-%d', validators=[DataRequired()])
    xp_reward = IntegerField('XP Reward', default=50)
    description = TextAreaField('Description')