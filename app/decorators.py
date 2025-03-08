from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    Decorator for routes that require admin access.
    Redirects to home page if user is not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function 