import json
import os
from app import create_app, db
from app.models.assessment import Assessment, AssessmentResult

def initialize_assessment():
    """Initialize the database with the Social Styles Assessment."""
    app = create_app(os.getenv('FLASK_CONFIG', 'development'))
    
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        try:
            # Check if assessment already exists
            existing_assessment = Assessment.query.first()
            
            if existing_assessment:
                # Delete any existing assessment results that reference this assessment
                AssessmentResult.query.filter_by(assessment_id=existing_assessment.id).delete()
                # Delete the existing assessment
                db.session.delete(existing_assessment)
                db.session.commit()
                print("Existing assessment and related results deleted.")
        except Exception as e:
            # Handle the case where the table doesn't exist yet
            print(f"Note: {e}")
            db.session.rollback()
        
        # Create the Social Styles assessment with the exact format from the image
        questions = [
            # Assertiveness questions (15 pairs)
            {"id": 1, "text": "I perceive myself as:", "left_label": "Quiet", "right_label": "Talkative", "category": "assertiveness"},
            {"id": 2, "text": "I perceive myself as:", "left_label": "Slow to Decide", "right_label": "Fast to Decide", "category": "assertiveness"},
            {"id": 3, "text": "I perceive myself as:", "left_label": "Going along", "right_label": "Taking charge", "category": "assertiveness"},
            {"id": 4, "text": "I perceive myself as:", "left_label": "Supportive", "right_label": "Challenging", "category": "assertiveness"},
            {"id": 5, "text": "I perceive myself as:", "left_label": "Compliant", "right_label": "Dominant", "category": "assertiveness"},
            {"id": 6, "text": "I perceive myself as:", "left_label": "Deliberate", "right_label": "Fast to Decide", "category": "assertiveness"},
            {"id": 7, "text": "I perceive myself as:", "left_label": "Asking questions", "right_label": "Making statements", "category": "assertiveness"},
            {"id": 8, "text": "I perceive myself as:", "left_label": "Cooperative", "right_label": "Competitive", "category": "assertiveness"},
            {"id": 9, "text": "I perceive myself as:", "left_label": "Avoiding risks", "right_label": "Taking risks", "category": "assertiveness"},
            {"id": 10, "text": "I perceive myself as:", "left_label": "Slow, studied", "right_label": "Fast-paced", "category": "assertiveness"},
            {"id": 11, "text": "I perceive myself as:", "left_label": "Cautious", "right_label": "Carefree", "category": "assertiveness"},
            {"id": 12, "text": "I perceive myself as:", "left_label": "Indulgent", "right_label": "Firm", "category": "assertiveness"},
            {"id": 13, "text": "I perceive myself as:", "left_label": "Non-assertive", "right_label": "Assertive", "category": "assertiveness"},
            {"id": 14, "text": "I perceive myself as:", "left_label": "Mellow", "right_label": "Matter of fact", "category": "assertiveness"},
            {"id": 15, "text": "I perceive myself as:", "left_label": "Reserved", "right_label": "Outgoing", "category": "assertiveness"},
            
            # Responsiveness questions (15 pairs)
            {"id": 16, "text": "I perceive myself as:", "left_label": "Open", "right_label": "Closed", "category": "responsiveness"},
            {"id": 17, "text": "I perceive myself as:", "left_label": "Impulsive", "right_label": "Deliberate", "category": "responsiveness"},
            {"id": 18, "text": "I perceive myself as:", "left_label": "Using opinions", "right_label": "Using facts", "category": "responsiveness"},
            {"id": 19, "text": "I perceive myself as:", "left_label": "Informal", "right_label": "Formal", "category": "responsiveness"},
            {"id": 20, "text": "I perceive myself as:", "left_label": "Emotional", "right_label": "Unemotional", "category": "responsiveness"},
            {"id": 21, "text": "I perceive myself as:", "left_label": "Easy to know", "right_label": "Hard to know", "category": "responsiveness"},
            {"id": 22, "text": "I perceive myself as:", "left_label": "Warm", "right_label": "Cool", "category": "responsiveness"},
            {"id": 23, "text": "I perceive myself as:", "left_label": "Excitable", "right_label": "Calm", "category": "responsiveness"},
            {"id": 24, "text": "I perceive myself as:", "left_label": "Animated", "right_label": "Poker-faced", "category": "responsiveness"},
            {"id": 25, "text": "I perceive myself as:", "left_label": "People-oriented", "right_label": "Task-oriented", "category": "responsiveness"},
            {"id": 26, "text": "I perceive myself as:", "left_label": "Spontaneous", "right_label": "Cautious", "category": "responsiveness"},
            {"id": 27, "text": "I perceive myself as:", "left_label": "Responsive", "right_label": "Non-responsive", "category": "responsiveness"},
            {"id": 28, "text": "I perceive myself as:", "left_label": "Humorous", "right_label": "Serious", "category": "responsiveness"},
            {"id": 29, "text": "I perceive myself as:", "left_label": "Impulsive", "right_label": "Methodical", "category": "responsiveness"},
            {"id": 30, "text": "I perceive myself as:", "left_label": "Lighthearted", "right_label": "Intense", "category": "responsiveness"}
        ]
        
        assessment = Assessment(
            name="Social Styles Assessment",
            description="This assessment helps identify your social style based on assertiveness and responsiveness dimensions using the paired opposites format.",
            questions=json.dumps(questions)
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        print("Database initialized with updated Social Styles Assessment using paired opposites format.")

if __name__ == "__main__":
    initialize_assessment() 