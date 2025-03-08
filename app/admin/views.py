from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.admin import admin
from app.decorators import admin_required
from app.models.user import User
from app.models.assessment import Assessment, AssessmentResult
from app.email import send_email

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview statistics."""
    # Get user statistics
    total_users = User.query.count()
    active_users = User.query.filter(User.last_login > (datetime.utcnow() - timedelta(days=30))).count()
    
    # Get assessment statistics
    total_assessments = Assessment.query.count()
    total_results = AssessmentResult.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent assessment results
    recent_results = AssessmentResult.query.order_by(AssessmentResult.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          active_users=active_users,
                          total_assessments=total_assessments,
                          total_results=total_results,
                          recent_users=recent_users,
                          recent_results=recent_results)

@admin.route('/users')
@login_required
@admin_required
def users():
    """List all users with management options."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Show detailed information about a user."""
    user = User.query.get_or_404(user_id)
    results = AssessmentResult.query.filter_by(user_id=user.id).order_by(AssessmentResult.created_at.desc()).all()
    return render_template('admin/user_detail.html', user=user, results=results)

@admin.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user."""
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from yourself
    if user.id == current_user.id:
        flash('You cannot remove your own admin privileges.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Admin status for {user.name} has been {"granted" if user.is_admin else "revoked"}.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """Send password reset email to a user."""
    user = User.query.get_or_404(user_id)
    token = user.generate_reset_token()
    
    send_email(
        to=user.email,
        subject='Reset Your Password',
        template='auth/email/reset_password',
        user=user,
        reset_url=url_for('auth.password_reset', token=token, _external=True)
    )
    
    flash(f'Password reset email has been sent to {user.email}.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user.id))

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user and all their data."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Delete all assessment results for this user
    AssessmentResult.query.filter_by(user_id=user.id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.name} has been deleted.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/assessments')
@login_required
@admin_required
def assessments():
    """List all assessments with management options."""
    assessments = Assessment.query.order_by(Assessment.created_at.desc()).all()
    
    # Get social style distribution for all assessments
    style_distribution = db.session.query(
        AssessmentResult.social_style,
        func.count(AssessmentResult.id)
    ).group_by(AssessmentResult.social_style).all()
    
    # Convert to a dictionary for easier access in the template
    style_counts = {
        'DRIVER': 0,
        'EXPRESSIVE': 0,
        'AMIABLE': 0,
        'ANALYTICAL': 0
    }
    
    for style, count in style_distribution:
        if style in style_counts:
            style_counts[style] = count
    
    # Format for the template
    assessment_stats = {
        'style_counts': style_counts
    }
    
    return render_template('admin/assessments.html', 
                          assessments=assessments,
                          assessment_stats=assessment_stats)

@admin.route('/assessments/<int:assessment_id>')
@login_required
@admin_required
def assessment_detail(assessment_id):
    """Show detailed information about an assessment."""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Get statistics for this assessment
    total_results = AssessmentResult.query.filter_by(assessment_id=assessment.id).count()
    
    # Get distribution of social styles
    style_distribution = db.session.query(
        AssessmentResult.social_style, 
        func.count(AssessmentResult.id)
    ).filter_by(assessment_id=assessment.id).group_by(AssessmentResult.social_style).all()
    
    # Get recent results
    recent_results = AssessmentResult.query.filter_by(assessment_id=assessment.id).order_by(AssessmentResult.created_at.desc()).limit(10).all()
    
    return render_template('admin/assessment_detail.html', 
                          assessment=assessment,
                          total_results=total_results,
                          style_distribution=style_distribution,
                          recent_results=recent_results)

@admin.route('/assessments/<int:assessment_id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_assessment_active(assessment_id):
    """Toggle active status for an assessment."""
    assessment = Assessment.query.get_or_404(assessment_id)
    assessment.is_active = not assessment.is_active
    db.session.commit()
    
    flash(f'Assessment "{assessment.name}" has been {"activated" if assessment.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.assessments'))

@admin.route('/assessments/add', methods=['POST'])
@login_required
@admin_required
def add_assessment():
    """Add a new assessment."""
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name or not description:
        flash('Please provide both name and description.', 'danger')
        return redirect(url_for('admin.assessments'))
    
    assessment = Assessment(
        name=name,
        description=description,
        questions='[]',  # Empty JSON array for questions
        is_active=False  # Start as inactive until questions are added
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    flash(f'Assessment "{name}" has been created. Please add questions to activate it.', 'success')
    return redirect(url_for('admin.assessment_detail', assessment_id=assessment.id))

@admin.route('/assessments/<int:assessment_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_assessment(assessment_id):
    """Edit an assessment."""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name or not description:
        flash('Please provide both name and description.', 'danger')
        return redirect(url_for('admin.assessment_detail', assessment_id=assessment_id))
    
    assessment.name = name
    assessment.description = description
    db.session.commit()
    
    flash(f'Assessment "{name}" has been updated.', 'success')
    return redirect(url_for('admin.assessment_detail', assessment_id=assessment_id))

@admin.route('/statistics')
@login_required
@admin_required
def statistics():
    """Show detailed statistics about users and assessments."""
    # User statistics
    total_users = User.query.count()
    active_users_30d = User.query.filter(User.last_login > (datetime.utcnow() - timedelta(days=30))).count()
    active_users_7d = User.query.filter(User.last_login > (datetime.utcnow() - timedelta(days=7))).count()
    
    # Assessment statistics
    total_assessments = Assessment.query.count()
    total_results = AssessmentResult.query.count()
    
    # Results by month (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    results_by_month = db.session.query(
        func.strftime('%Y-%m', AssessmentResult.created_at).label('month'),
        func.count(AssessmentResult.id)
    ).filter(AssessmentResult.created_at > six_months_ago).group_by('month').order_by('month').all()
    
    # Social style distribution
    style_distribution = db.session.query(
        AssessmentResult.social_style,
        func.count(AssessmentResult.id)
    ).group_by(AssessmentResult.social_style).all()
    
    # User activity by day of week
    # Extract day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
    active_users_by_day = [0] * 7  # Initialize with zeros for all days
    
    # Query active users by day of week
    day_counts = db.session.query(
        func.strftime('%w', User.last_login).label('day_of_week'),
        func.count(User.id).label('count')
    ).filter(User.last_login.isnot(None)).group_by('day_of_week').all()
    
    # Fill in the counts
    for day, count in day_counts:
        if day is not None:
            day_index = int(day)
            active_users_by_day[day_index] = count
    
    return render_template('admin/statistics.html',
                          total_users=total_users,
                          active_users_30d=active_users_30d,
                          active_users_7d=active_users_7d,
                          total_assessments=total_assessments,
                          total_results=total_results,
                          results_by_month=results_by_month,
                          style_distribution=style_distribution,
                          active_users_by_day=active_users_by_day) 