from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from . import assessment
from .. import db
from ..models.assessment import Assessment, AssessmentResult
from .forms import AssessmentForm
from .utils import generate_pdf_report, generate_social_style_chart
import json
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

@assessment.route('/dashboard')
@login_required
def dashboard():
    """Display user's assessment history and results."""
    results = AssessmentResult.query.filter_by(user_id=current_user.id).order_by(
        AssessmentResult.created_at.desc()).all()
    
    return render_template('assessment/dashboard.html', results=results)

@assessment.route('/take/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
def take_assessment(assessment_id):
    """Take the Social Styles assessment."""
    assessment_obj = Assessment.query.get_or_404(assessment_id)
    questions = assessment_obj.get_questions()
    
    form = AssessmentForm()
    
    if form.validate_on_submit():
        # Process form data
        responses = {}
        for question in questions:
            question_id = str(question['id'])
            response_value = int(request.form.get(f'question_{question_id}', 0))
            responses[question_id] = response_value
        
        # Create new assessment result
        result = AssessmentResult(
            user_id=current_user.id,
            assessment_id=assessment_id
        )
        result.set_responses(responses)
        result.calculate_scores()
        
        db.session.add(result)
        db.session.commit()
        
        flash('Assessment completed successfully!', 'success')
        return redirect(url_for('assessment.results', result_id=result.id))
    
    return render_template('assessment/take.html', 
                          assessment=assessment_obj, 
                          questions=questions,
                          form=form)

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