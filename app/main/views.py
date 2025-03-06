from flask import render_template, redirect, url_for
from flask_login import current_user
from . import main

@main.route('/')
def index():
    """Render the homepage."""
    return render_template('main/index.html')

@main.route('/about')
def about():
    """Render the about page with information about Social Styles."""
    return render_template('main/about.html')

@main.route('/dashboard')
def dashboard():
    """Redirect to user dashboard if logged in, otherwise to homepage."""
    if current_user.is_authenticated:
        return redirect(url_for('assessment.dashboard'))
    return redirect(url_for('main.index')) 