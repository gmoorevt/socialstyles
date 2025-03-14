from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, abort, session
from flask_login import login_required, current_user, login_user
from app import db
from app.team import team
from app.models import Team, TeamMember, TeamInvite, User, Assessment
from app.team.forms import TeamForm, InviteMembersForm, QuickRegisterForm
from app.email import send_email
import qrcode
from io import BytesIO
import base64
from werkzeug.security import generate_password_hash

@team.route('/teams')
@login_required
def list_teams():
    """List all teams for the current user"""
    user_teams = current_user.get_teams()
    owned_teams = current_user.owned_teams.all()
    
    return render_template('team/teams.html', 
                          user_teams=user_teams,
                          owned_teams=owned_teams,
                          title='My Teams')

@team.route('/teams/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """Create a new team"""
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(
            name=form.name.data,
            description=form.description.data,
            owner_id=current_user.id
        )
        db.session.add(team)
        db.session.flush()  # Get team ID without committing transaction
        
        # Add current user as team owner
        team_member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role='owner'
        )
        db.session.add(team_member)
        
        # Process initial invites if provided
        if form.initial_members.data:
            emails = [email.strip() for email in form.initial_members.data.split(',')]
            for email in emails:
                if email and email != current_user.email:  # Skip empty emails and current user
                    invite = TeamInvite(
                        team_id=team.id,
                        email=email,
                    )
                    db.session.add(invite)
                    send_team_invitation(invite)
        
        db.session.commit()
        flash(f'Team "{team.name}" created successfully!', 'success')
        return redirect(url_for('team.view_team', team_id=team.id))
    
    return render_template('team/create_team.html', form=form, title='Create Team')

@team.route('/teams/<int:team_id>')
@login_required
def view_team(team_id):
    """View a specific team"""
    team = Team.query.get_or_404(team_id)
    
    if not team.is_member(current_user) and not current_user.is_admin:
        flash('You are not a member of this team.', 'danger')
        return redirect(url_for('team.list_teams'))
    
    # Get all team members with their latest assessment results
    team_members = []
    for membership in team.members.all():
        user = User.query.get(membership.user_id)
        latest_result = user.get_latest_assessment_result()
        team_members.append({
            'user': user,
            'role': membership.role,
            'joined_at': membership.joined_at,
            'latest_result': latest_result
        })
    
    # Note: No longer displaying pending invites as they're auto-accepted
    is_owner = team.is_owner(current_user)
    
    return render_template('team/view_team.html',
                          team=team,
                          members=team_members,
                          is_owner=is_owner,
                          title=team.name)

@team.route('/teams/<int:team_id>/invite', methods=['GET', 'POST'])
@login_required
def invite_members(team_id):
    """Invite members to a team"""
    team = Team.query.get_or_404(team_id)
    
    if not team.is_owner(current_user) and not current_user.is_admin:
        flash('Only the team owner can invite new members.', 'danger')
        return redirect(url_for('team.view_team', team_id=team.id))
    
    form = InviteMembersForm()
    if form.validate_on_submit():
        emails = [email.strip() for email in form.emails.data.split(',')]
        users_added = 0
        invites_sent = 0
        
        for email in emails:
            if email:
                # Check if already a member
                user = User.query.filter_by(email=email).first()
                if user and team.is_member(user):
                    flash(f'{email} is already a member of this team.', 'info')
                    continue
                
                # If user exists, add them directly to the team
                if user:
                    team.add_member(user)
                    users_added += 1
                    # Send notification email
                    send_team_notification(team, user.email)
                else:
                    # Check if invitation already exists
                    existing_invite = TeamInvite.query.filter_by(
                        team_id=team.id, 
                        email=email, 
                        status='pending'
                    ).first()
                    
                    if existing_invite:
                        flash(f'An invitation for {email} is already pending.', 'info')
                        continue
                    
                    # Create and send invitation for users who don't have accounts yet
                    invite = TeamInvite(
                        team_id=team.id,
                        email=email,
                        status='auto_accepted'  # Mark as auto-accepted
                    )
                    db.session.add(invite)
                    send_team_invitation(invite)
                    invites_sent += 1
        
        db.session.commit()
        
        if users_added > 0:
            flash(f'{users_added} users have been added to the team!', 'success')
        
        if invites_sent > 0:
            flash(f'{invites_sent} invitations sent to users who don\'t have accounts yet.', 'success')
        
        return redirect(url_for('team.view_team', team_id=team.id))
    
    return render_template('team/invite_members.html', 
                          team=team,
                          form=form,
                          title=f'Invite to {team.name}')

@team.route('/teams/<int:team_id>/dashboard')
@login_required
def team_dashboard(team_id):
    """View the team dashboard with all members' assessment results"""
    team = Team.query.get_or_404(team_id)
    
    if not team.is_member(current_user) and not current_user.is_admin:
        flash('You are not a member of this team.', 'danger')
        return redirect(url_for('team.list_teams'))
    
    # Get all team members with their latest assessment results
    team_members = []
    for membership in team.members.all():
        user = User.query.get(membership.user_id)
        latest_result = user.get_latest_assessment_result()
        if latest_result:  # Only include members with completed assessments
            team_members.append({
                'user': user,
                'result': latest_result
            })
    
    # Generate the team join QR code with Base62 token
    token = team.generate_join_token()
    join_url = url_for('team.quick_join', token=token, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(join_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    qr_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return render_template('team/dashboard.html',
                          team=team,
                          members=team_members,
                          qr_image=qr_image,
                          join_url=join_url,
                          title=f'{team.name} Dashboard')

@team.route('/teams/<int:team_id>/present')
@login_required
def team_presentation(team_id):
    """View the team presentation mode designed for projection"""
    team = Team.query.get_or_404(team_id)
    
    if not team.is_member(current_user) and not current_user.is_admin:
        flash('You are not a member of this team.', 'danger')
        return redirect(url_for('team.list_teams'))
    
    # Get all team members with their latest assessment results
    team_members = []
    for membership in team.members.all():
        user = User.query.get(membership.user_id)
        latest_result = user.get_latest_assessment_result()
        if latest_result:  # Only include members with completed assessments
            team_members.append({
                'user': user,
                'result': latest_result
            })
    
    # Generate the team join QR code with Base62 token
    token = team.generate_join_token()
    join_url = url_for('team.quick_join', token=token, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(join_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    qr_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Include dashboard grid data for the presentation view
    # The grid data will be passed to the template for cleaner display
    return render_template('team/presentation.html',
                          team=team,
                          members=team_members,
                          qr_image=qr_image,
                          join_url=join_url,
                          team_id=team.id,
                          title=f'{team.name} - Presentation')

@team.route('/teams/<int:team_id>/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_member(team_id, user_id):
    """Remove a member from the team"""
    team = Team.query.get_or_404(team_id)
    
    if not team.is_owner(current_user) and not current_user.is_admin:
        flash('Only the team owner can remove members.', 'danger')
        return redirect(url_for('team.view_team', team_id=team.id))
    
    user = User.query.get_or_404(user_id)
    
    # Cannot remove the owner
    if team.is_owner(user):
        flash('Cannot remove the team owner.', 'danger')
        return redirect(url_for('team.view_team', team_id=team.id))
    
    if team.remove_member(user):
        db.session.commit()
        flash(f'{user.name or user.email} has been removed from the team.', 'success')
    else:
        flash('Failed to remove member. Please try again.', 'danger')
    
    return redirect(url_for('team.view_team', team_id=team.id))

@team.route('/teams/<int:team_id>/leave', methods=['POST'])
@login_required
def leave_team(team_id):
    """Leave a team"""
    team = Team.query.get_or_404(team_id)
    
    if team.is_owner(current_user):
        flash('The team owner cannot leave the team. Transfer ownership first or delete the team.', 'danger')
        return redirect(url_for('team.view_team', team_id=team.id))
    
    if team.remove_member(current_user):
        db.session.commit()
        flash(f'You have left the team {team.name}.', 'success')
    else:
        flash('Failed to leave the team. Please try again.', 'danger')
    
    return redirect(url_for('team.list_teams'))

@team.route('/teams/<int:team_id>/delete', methods=['POST'])
@login_required
def delete_team(team_id):
    """Delete a team (owner only)"""
    team = Team.query.get_or_404(team_id)
    
    if not team.is_owner(current_user) and not current_user.is_admin:
        flash('Only the team owner can delete the team.', 'danger')
        return redirect(url_for('team.view_team', team_id=team.id))
    
    team_name = team.name
    db.session.delete(team)
    db.session.commit()
    
    flash(f'Team "{team_name}" has been deleted.', 'success')
    return redirect(url_for('team.list_teams'))

@team.route('/join/<token>')
def join(token):
    """Join a team using a token - redirects to quick_join with appropriate parameters"""
    try:
        # Parse the Base62 token
        parts = token.split('-')
        if len(parts) >= 2:
            # Extract team name from token if present
            team_name = parts[2].replace('_', ' ') if len(parts) > 2 else None
            
            # Find team by name or redirect to teams list
            team = None
            if team_name:
                team = Team.query.filter_by(name=team_name).first()
            
            if team:
                return redirect(url_for('team.quick_join', token=token))
    except Exception as e:
        current_app.logger.error(f"Error parsing join token: {e}")
    
    flash('Invalid or expired join link. Please ask for a new invitation.', 'danger')
    return redirect(url_for('main.index'))

def send_team_invitation(invite):
    """Send a team invitation email"""
    team = Team.query.get(invite.team_id)
    
    # Use a direct link to take the assessment instead of an acceptance link
    token_url = url_for('team.join', token=team.generate_join_token(), _external=True)
    
    send_email(
        to=invite.email,
        subject=f"You've been added to the {team.name} team",
        template='team/email/auto_added',
        team=team,
        token_url=token_url
    )
    
    return True

def send_team_notification(team, email):
    """Send a notification that the user has been added to a team"""
    # Generate a direct link to the team
    team_url = url_for('team.view_team', team_id=team.id, _external=True)
    
    send_email(
        to=email,
        subject=f"You've been added to the {team.name} team",
        template='team/email/auto_added',
        team=team,
        token_url=team_url
    )
    
    return True

@team.route('/quick-join/<token>', methods=['GET', 'POST'])
def quick_join(token):
    """Streamlined join process initiated from QR code or join link using Base62 token"""
    try:
        # Parse the Base62 token
        parts = token.split('-')
        team_name = parts[2].replace('_', ' ') if len(parts) > 2 else None
        
        # Find team by name
        team = None
        if team_name:
            team = Team.query.filter_by(name=team_name).first()
        
        if not team:
            flash('Invalid team link. Please ask for a new invitation.', 'danger')
            return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Error parsing join token: {e}")
        flash('Invalid team link. Please ask for a new invitation.', 'danger')
        return redirect(url_for('main.index'))
    
    # If user is already logged in
    if current_user.is_authenticated:
        # If already a member of this team, go to assessment
        if team.is_member(current_user):
            return redirect(url_for('assessment.take_assessment', assessment_id=1))
        # If not a member, add them to the team without confirmation
        else:
            team.add_member(current_user)
            db.session.commit()
            flash(f'You have been added to the team "{team.name}"!', 'success')
            return redirect(url_for('assessment.take_assessment', assessment_id=1))
    
    # Store the team ID in session for use in post-assessment
    session['pending_team_join'] = team.id
    
    # For new or not logged in users
    form = QuickRegisterForm()
    if form.validate_on_submit():
        # Save the user information in session for later registration
        session['quick_register_name'] = form.name.data
        session['quick_register_email'] = form.email.data
        session['quick_register_team_id'] = team.id
        
        # Check if user exists
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # If user exists, associate with assessment and redirect to login
            flash('An account with this email already exists. Please log in to continue.', 'info')
            return redirect(url_for('auth.login', next=url_for('assessment.take_assessment', assessment_id=1)))
        else:
            # New user - proceed directly to assessment
            # We'll register them after assessment if they want
            return redirect(url_for('assessment.take_assessment', assessment_id=1, guest=True))
    
    return render_template('team/quick_register.html', 
                           form=form, 
                           team=team,
                           title='Join Team')

@team.route('/set-password', methods=['GET', 'POST'])
@login_required
def set_password():
    """Allow users to set their password after completing assessment via QR code"""
    # If user doesn't need to set password, redirect to dashboard
    if not session.get('needs_password_setup'):
        return redirect(url_for('assessment.dashboard'))
    
    from app.auth.forms import PasswordForm
    form = PasswordForm()
    
    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.commit()
        
        # Clear the session flags
        session.pop('needs_password_setup', None)
        team_id = session.pop('from_team_join', None)
        
        flash('Your password has been set successfully!', 'success')
        
        # If they came from a team join, show them the team dashboard
        if team_id:
            return redirect(url_for('team.team_dashboard', team_id=team_id))
        else:
            return redirect(url_for('assessment.dashboard'))
    
    return render_template('team/set_password.html', form=form, title='Set Your Password') 