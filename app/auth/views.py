from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models.user import User
from .forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm
from ..email import send_email
from datetime import datetime

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            user.update_last_login()  # Update last login time
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            name=form.name.data,
            password=form.password.data,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        flash('You have been registered successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    """Route for requesting a password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        token = user.generate_reset_token()
        
        send_email(
            to=user.email,
            subject='Reset Your Password',
            template='auth/email/reset_password',
            user=user,
            reset_url=url_for('auth.reset_password', token=token, _external=True)
        )
        
        flash('An email with instructions to reset your password has been sent to you.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_request.html', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Route for resetting password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Your password has been updated! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form) 