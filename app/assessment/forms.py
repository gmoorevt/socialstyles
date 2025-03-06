from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired

class AssessmentForm(FlaskForm):
    """Form for taking the Social Styles assessment.
    
    Note: The actual question fields will be dynamically generated in the template
    based on the assessment questions from the database.
    """
    submit = SubmitField('Submit Assessment') 