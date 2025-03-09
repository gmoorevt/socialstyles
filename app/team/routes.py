from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.team import team
from app.models import Team, TeamMember, TeamInvite, User
from app.team.forms import TeamForm, InviteMembersForm
from app.email import send_email
import qrcode
from io import BytesIO
import base64

@team.route('/teams')
@login_required
def list_teams():
    """List all teams for the current user"""
    user_teams = current_user.get_teams()
    owned_teams = current_user.owned_teams.all()
    pending_invites = TeamInvite.query.filter_by(email=current_user.email, status='pending').all()
    
    return render_template('team/teams.html', 
                          user_teams=user_teams,
                          owned_teams=owned_teams,
                          pending_invites=pending_invites,
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
    
    pending_invites = team.invites.filter_by(status='pending').all()
    is_owner = team.is_owner(current_user)
    
    return render_template('team/view_team.html',
                          team=team,
                          members=team_members,
                          pending_invites=pending_invites,
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
        invites_sent = 0
        
        for email in emails:
            if email:
                # Check if already a member
                user = User.query.filter_by(email=email).first()
                if user and team.is_member(user):
                    flash(f'{email} is already a member of this team.', 'info')
                    continue
                
                # Check if invitation already exists
                existing_invite = TeamInvite.query.filter_by(
                    team_id=team.id, 
                    email=email, 
                    status='pending'
                ).first()
                
                if existing_invite:
                    flash(f'An invitation for {email} is already pending.', 'info')
                    continue
                
                # Create and send invitation
                invite = TeamInvite(
                    team_id=team.id,
                    email=email,
                )
                db.session.add(invite)
                send_team_invitation(invite)
                invites_sent += 1
        
        db.session.commit()
        
        if invites_sent > 0:
            flash(f'{invites_sent} invitations sent successfully!', 'success')
        
        return redirect(url_for('team.view_team', team_id=team.id))
    
    return render_template('team/invite_members.html', 
                          team=team,
                          form=form,
                          title=f'Invite to {team.name}')

@team.route('/invites/<token>/accept')
@login_required
def accept_invite(token):
    """Accept a team invitation"""
    invite = TeamInvite.query.filter_by(token=token).first_or_404()
    
    if invite.status != 'pending':
        flash('This invitation has already been processed.', 'info')
        return redirect(url_for('team.list_teams'))
    
    if invite.is_expired:
        flash('This invitation has expired.', 'danger')
        return redirect(url_for('team.list_teams'))
    
    if invite.email != current_user.email:
        flash('This invitation was sent to a different email address.', 'danger')
        return redirect(url_for('team.list_teams'))
    
    if invite.accept(current_user):
        db.session.commit()
        flash('You have successfully joined the team!', 'success')
        return redirect(url_for('team.view_team', team_id=invite.team_id))
    else:
        flash('Failed to join the team. Please try again.', 'danger')
        return redirect(url_for('team.list_teams'))

@team.route('/invites/<token>/reject')
@login_required
def reject_invite(token):
    """Reject a team invitation"""
    invite = TeamInvite.query.filter_by(token=token).first_or_404()
    
    if invite.email != current_user.email:
        flash('This invitation was sent to a different email address.', 'danger')
        return redirect(url_for('team.list_teams'))
    
    if invite.reject():
        db.session.commit()
        flash('Invitation rejected.', 'info')
    
    return redirect(url_for('team.list_teams'))

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
    
    # Generate the team join QR code
    join_url = team.get_join_url()
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
    
    # Generate the team join QR code
    join_url = team.get_join_url()
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
    
    return render_template('team/presentation.html',
                          team=team,
                          members=team_members,
                          qr_image=qr_image,
                          join_url=join_url,
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
@login_required
def join(token):
    """Join a team via token"""
    # First, check if it's an invitation token
    invite = TeamInvite.query.filter_by(token=token).first()
    if invite:
        # Handle as a regular invitation
        if invite.email == current_user.email:
            return redirect(url_for('team.accept_invite', token=token))
        else:
            flash('This invitation was sent to a different email address.', 'danger')
            return redirect(url_for('team.list_teams'))
    
    # If not an invitation, try to find the team by a join token
    # This would require additional logic to store and validate join tokens
    # For this implementation, we'll just show an error
    flash('Invalid or expired join link. Please ask for a new invitation.', 'danger')
    return redirect(url_for('team.list_teams'))

def send_team_invitation(invite):
    """Send a team invitation email"""
    team = Team.query.get(invite.team_id)
    token_url = url_for('team.accept_invite', token=invite.token, _external=True)
    
    html = render_template('team/email/invitation.html',
                         team=team,
                         token_url=token_url)
    
    subject = f"Invitation to join {team.name} team"
    
    send_email(subject, 
              recipients=[invite.email],
              html_body=html)
    
    return True 