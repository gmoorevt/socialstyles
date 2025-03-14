from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, session
from flask_login import login_required, current_user, login_user
from . import assessment
from .. import db
from ..models.assessment import Assessment, AssessmentResult
from ..models.user import User
from .forms import AssessmentForm
from ..auth.forms import RegistrationForm
from .utils import generate_pdf_report, generate_social_style_chart
from werkzeug.security import generate_password_hash
from ..websockets.events import broadcast_new_assessment
import json
import io
import matplotlib
import uuid
matplotlib.use('Agg')  # Use non-interactive backend

@assessment.route('/dashboard')
@login_required
def dashboard():
    """Display user's assessment history and results."""
    results = AssessmentResult.query.filter_by(user_id=current_user.id).order_by(
        AssessmentResult.created_at.desc()).all()
    
    return render_template('assessment/dashboard.html', results=results)

@assessment.route('/take/<int:assessment_id>', methods=['GET', 'POST'])
def take_assessment(assessment_id):
    """Take the Social Styles assessment. Available for both logged-in and guest users."""
    assessment_obj = Assessment.query.get_or_404(assessment_id)
    questions = assessment_obj.get_questions()
    
    # Check if this is a guest user
    is_guest = request.args.get('guest') == 'True' or request.args.get('guest') == 'true'
    
    # Separate questions by category
    assertiveness_questions = []
    responsiveness_questions = []
    
    for question in questions:
        # Rename keys to match template expectations
        question['left_characteristic'] = question.get('left_label', '')
        question['right_characteristic'] = question.get('right_label', '')
        
        if question.get('category') == 'assertiveness':
            assertiveness_questions.append(question)
        elif question.get('category') == 'responsiveness':
            responsiveness_questions.append(question)
    
    form = AssessmentForm()
    
    if form.validate_on_submit():
        # Process form data
        responses = {}
        
        # Process assertiveness questions
        for question in assertiveness_questions:
            question_id = str(question['id'])
            response_value = int(request.form.get(f'assertiveness_{question_id}', 0))
            responses[question_id] = response_value
        
        # Process responsiveness questions
        for question in responsiveness_questions:
            question_id = str(question['id'])
            response_value = int(request.form.get(f'responsiveness_{question_id}', 0))
            responses[question_id] = response_value
        
        # If user is logged in, save normally
        if current_user.is_authenticated:
            result = AssessmentResult(
                user_id=current_user.id,
                assessment_id=assessment_id
            )
            result.set_responses(responses)
            result.calculate_scores()
            
            db.session.add(result)
            db.session.commit()
            
            # Broadcast the new result to team members if user is part of a team
            from app.models.team import TeamMember
            team_memberships = TeamMember.query.filter_by(user_id=current_user.id).all()
            for membership in team_memberships:
                broadcast_new_assessment(
                    team_id=membership.team_id,
                    user_id=current_user.id,
                    user_name=current_user.name or current_user.email,
                    assertiveness_score=result.assertiveness_score,
                    responsiveness_score=result.responsiveness_score
                )
            
            flash('Assessment completed successfully!', 'success')
            return redirect(url_for('assessment.results', result_id=result.id))
        else:
            # For guest users, store results in session for later association
            session['guest_responses'] = responses
            session['guest_assessment_id'] = assessment_id
            
            # Calculate scores but don't save to database yet
            temp_result = AssessmentResult(assessment_id=assessment_id)
            temp_result.set_responses(responses)
            temp_result.calculate_scores()
            
            # Store the scores in session
            session['guest_assertiveness_score'] = temp_result.assertiveness_score
            session['guest_responsiveness_score'] = temp_result.responsiveness_score
            
            # Redirect to post-assessment page where they can choose to register
            return redirect(url_for('assessment.post_assessment'))
    
    return render_template('assessment/take.html', 
                          assessment=assessment_obj, 
                          assertiveness_questions=assertiveness_questions,
                          responsiveness_questions=responsiveness_questions,
                          form=form,
                          is_guest=is_guest)

@assessment.route('/post-assessment', methods=['GET', 'POST'])
def post_assessment():
    """Page shown after a guest completes an assessment, offering registration."""
    # Ensure we have guest assessment data
    if not session.get('guest_responses'):
        flash('No assessment data found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Generate chart for the guest's results
    chart_img = generate_social_style_chart(
        session.get('guest_assertiveness_score'), 
        session.get('guest_responsiveness_score')
    )
    
    form = RegistrationForm()
    
    # Pre-fill form with data if it was provided during quick registration
    if session.get('quick_register_name') and session.get('quick_register_email'):
        form.name.data = session.get('quick_register_name')
        form.email.data = session.get('quick_register_email')
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        
        if existing_user:
            # Associate the assessment with existing user
            result = AssessmentResult(
                user_id=existing_user.id,
                assessment_id=session.get('guest_assessment_id')
            )
            result.set_responses(session.get('guest_responses'))
            result.calculate_scores()
            
            db.session.add(result)
            
            # If there was a pending team join
            if session.get('pending_team_join'):
                from app.models.team import Team, TeamMember
                team = Team.query.get(session.get('pending_team_join'))
                if team and not team.is_member(existing_user):
                    team.add_member(existing_user)
                    
                    # Broadcast the new result to team members
                    broadcast_new_assessment(
                        team_id=team.id,
                        user_id=existing_user.id,
                        user_name=existing_user.name or existing_user.email,
                        assertiveness_score=result.assertiveness_score,
                        responsiveness_score=result.responsiveness_score
                    )
            
            db.session.commit()
            
            # Log in the user
            login_user(existing_user)
            
            # Clear session data
            session.pop('guest_responses', None)
            session.pop('guest_assessment_id', None)
            session.pop('guest_assertiveness_score', None)
            session.pop('guest_responsiveness_score', None)
            session.pop('quick_register_name', None)
            session.pop('quick_register_email', None)
            session.pop('pending_team_join', None)
            
            flash('Your assessment has been saved to your account!', 'success')
            return redirect(url_for('assessment.results', result_id=result.id))
        else:
            # Create new user and associate assessment
            new_user = User(
                email=form.email.data,
                name=form.name.data,
                password_hash=generate_password_hash(form.password.data)
            )
            db.session.add(new_user)
            db.session.flush()  # Get user ID without committing
            
            # Create and associate the assessment result
            result = AssessmentResult(
                user_id=new_user.id,
                assessment_id=session.get('guest_assessment_id')
            )
            result.set_responses(session.get('guest_responses'))
            result.calculate_scores()
            
            db.session.add(result)
            
            # If there was a pending team join
            if session.get('pending_team_join'):
                from app.models.team import Team
                team = Team.query.get(session.get('pending_team_join'))
                if team:
                    team.add_member(new_user)
                    
                    # Broadcast the new result to team members
                    broadcast_new_assessment(
                        team_id=team.id,
                        user_id=new_user.id,
                        user_name=new_user.name or new_user.email,
                        assertiveness_score=result.assertiveness_score,
                        responsiveness_score=result.responsiveness_score
                    )
            
            db.session.commit()
            
            # Log in the new user
            login_user(new_user)
            
            # Clear session data
            session.pop('guest_responses', None)
            session.pop('guest_assessment_id', None)
            session.pop('guest_assertiveness_score', None)
            session.pop('guest_responsiveness_score', None)
            session.pop('quick_register_name', None)
            session.pop('quick_register_email', None)
            session.pop('pending_team_join', None)
            
            flash('Account created successfully! Your assessment has been saved.', 'success')
            return redirect(url_for('assessment.results', result_id=result.id))
    
    # Provide options to register or continue as guest
    return render_template('assessment/post_assessment.html', 
                          form=form,
                          chart_img=chart_img,
                          assertiveness_score=session.get('guest_assertiveness_score'),
                          responsiveness_score=session.get('guest_responsiveness_score'))

@assessment.route('/continue-without-saving', methods=['GET'])
def continue_without_saving():
    """Handle the case when a user chooses not to save their results but we still want to associate with team."""
    # Check if we have all the required data
    if not session.get('guest_responses') or not session.get('guest_assessment_id'):
        flash('No assessment data found.', 'warning')
        return redirect(url_for('main.index'))
    
    # Create anonymous user if there's a pending team join
    if session.get('pending_team_join') and session.get('quick_register_name') and session.get('quick_register_email'):
        from app.models.team import Team
        team = Team.query.get(session.get('pending_team_join'))
        
        if team:
            # First check if a user already exists with this email
            email = session.get('quick_register_email')
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create an anonymous user with the provided name/email but no password
                display_name = session.get('quick_register_name')
                user = User(
                    email=email,
                    name=display_name,
                    password_hash=generate_password_hash(str(uuid.uuid4())),  # Random password they can't use
                    is_anonymous_assessment=True  # Flag this as an anonymous assessment user
                )
                db.session.add(user)
                db.session.flush()  # Get user ID without committing
            
            # Create and save the assessment result
            result = AssessmentResult(
                user_id=user.id,
                assessment_id=session.get('guest_assessment_id')
            )
            result.set_responses(session.get('guest_responses'))
            result.calculate_scores()
            db.session.add(result)
            
            # Add user to team if not already a member
            if not team.is_member(user):
                team.add_member(user)
            
            # Broadcast the new assessment result for the presentation view
            broadcast_new_assessment(
                team_id=team.id,
                user_id=user.id,
                user_name=user.name or user.email,
                assertiveness_score=result.assertiveness_score,
                responsiveness_score=result.responsiveness_score
            )
            
            db.session.commit()
            
            # Success message
            flash('Thank you for completing the assessment!', 'success')
    
    # Clear session data
    session.pop('guest_responses', None)
    session.pop('guest_assessment_id', None)
    session.pop('guest_assertiveness_score', None)
    session.pop('guest_responsiveness_score', None)
    session.pop('quick_register_name', None)
    session.pop('quick_register_email', None)
    session.pop('pending_team_join', None)
    
    return redirect(url_for('main.index'))

@assessment.route('/results/<int:result_id>')
@login_required
def results(result_id):
    """Display assessment results."""
    result = AssessmentResult.query.get_or_404(result_id)
    
    # Ensure the result belongs to the current user
    if result.user_id != current_user.id:
        flash('You do not have permission to view these results.', 'danger')
        return redirect(url_for('assessment.dashboard'))
    
    # Generate chart
    chart_img = generate_social_style_chart(result.assertiveness_score, result.responsiveness_score)
    
    # Check if user needs to set password (from QR code quick registration)
    if session.get('needs_password_setup'):
        flash('Please set a password to secure your account.', 'info')
        return redirect(url_for('team.set_password'))
    
    return render_template('assessment/results.html', 
                          result=result,
                          chart_img=chart_img)

@assessment.route('/download_report/<int:result_id>')
@login_required
def download_report(result_id):
    """Generate and download PDF report of assessment results."""
    result = AssessmentResult.query.get_or_404(result_id)
    
    # Ensure the result belongs to the current user
    if result.user_id != current_user.id:
        flash('You do not have permission to download this report.', 'danger')
        return redirect(url_for('assessment.dashboard'))
    
    # Generate chart
    chart_img = generate_social_style_chart(result.assertiveness_score, result.responsiveness_score)
    
    # Generate PDF report
    pdf_buffer = generate_pdf_report(result, chart_img, current_user)
    
    # Send the PDF as a downloadable file
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"social_styles_report_{result.id}.pdf",
        mimetype='application/pdf'
    )

@assessment.route('/list')
@login_required
def list_assessments():
    """List available assessments."""
    assessments = Assessment.query.all()
    return render_template('assessment/list.html', assessments=assessments)

@assessment.route('/delete_result/<int:result_id>', methods=['POST'])
@login_required
def delete_result(result_id):
    """Delete an assessment result."""
    result = AssessmentResult.query.get_or_404(result_id)
    
    # Ensure the user can only delete their own results
    if result.user_id != current_user.id:
        flash('You do not have permission to delete this result.', 'danger')
        return redirect(url_for('assessment.dashboard'))
    
    # Store information for the flash message
    assessment_name = result.assessment.name
    date_taken = result.created_at.strftime('%b %d, %Y')
    
    # Delete the result
    db.session.delete(result)
    db.session.commit()
    
    flash(f'Your assessment result for "{assessment_name}" taken on {date_taken} has been deleted.', 'success')
    return redirect(url_for('assessment.dashboard')) 