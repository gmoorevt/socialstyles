from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class TeamForm(FlaskForm):
    """Form for creating a new team"""
    name = StringField('Team Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    initial_members = StringField('Initial Members (comma-separated emails)', 
                                validators=[Optional()],
                                description="Separate multiple email addresses with commas")
    submit = SubmitField('Create Team')

class InviteMembersForm(FlaskForm):
    """Form for inviting members to a team"""
    emails = StringField('Email Addresses', 
                       validators=[DataRequired()],
                       description="Separate multiple email addresses with commas")
    submit = SubmitField('Send Invitations') 