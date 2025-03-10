from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

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

class QuickRegisterForm(FlaskForm):
    """Simplified registration form for users joining via QR code"""
    name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Continue to Assessment')

class PasswordForm(FlaskForm):
    """Form for setting a password after completing an assessment"""
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Set Password') 