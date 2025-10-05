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
        
        # Create the Social Styles assessment with improved Likert scale questions
        questions = [
            # Assertiveness questions (1-15)
            {"id": 1, "text": "I typically take charge in group situations.", "category": "assertiveness", "format": "likert"},
            {"id": 2, "text": "When I have an opinion, I express it directly.", "category": "assertiveness", "format": "likert"},
            {"id": 3, "text": "I make decisions quickly and confidently.", "category": "assertiveness", "format": "likert"},
            {"id": 4, "text": "I prefer to lead rather than follow.", "category": "assertiveness", "format": "likert"},
            {"id": 5, "text": "I am comfortable challenging others' ideas.", "category": "assertiveness", "format": "likert"},
            {"id": 6, "text": "I am direct in my communication style.", "category": "assertiveness", "format": "likert"},
            {"id": 7, "text": "When something needs to be done, I take immediate action.", "category": "assertiveness", "format": "likert"},
            {"id": 8, "text": "I am comfortable setting the agenda for meetings or gatherings.", "category": "assertiveness", "format": "likert"},
            {"id": 9, "text": "I often find myself influencing others' opinions.", "category": "assertiveness", "format": "likert"},
            {"id": 10, "text": "I prefer making statements rather than asking questions.", "category": "assertiveness", "format": "likert"},
            {"id": 11, "text": "I typically speak up in group settings.", "category": "assertiveness", "format": "likert"},
            {"id": 12, "text": "I am comfortable with conflict when necessary.", "category": "assertiveness", "format": "likert"},
            {"id": 13, "text": "I often take initiative on projects or tasks.", "category": "assertiveness", "format": "likert"},
            {"id": 14, "text": "When I want something, I ask for it directly.", "category": "assertiveness", "format": "likert"},
            {"id": 15, "text": "I am not afraid to take risks.", "category": "assertiveness", "format": "likert"},

            # Responsiveness questions (16-30)
            {"id": 16, "text": "I easily show my emotions to others.", "category": "responsiveness", "format": "likert"},
            {"id": 17, "text": "Building relationships is a priority for me in work settings.", "category": "responsiveness", "format": "likert"},
            {"id": 18, "text": "I pay close attention to how others are feeling.", "category": "responsiveness", "format": "likert"},
            {"id": 19, "text": "I am warm and friendly in my interactions.", "category": "responsiveness", "format": "likert"},
            {"id": 20, "text": "I value harmony in my relationships.", "category": "responsiveness", "format": "likert"},
            {"id": 21, "text": "I am animated when communicating with others.", "category": "responsiveness", "format": "likert"},
            {"id": 22, "text": "I tend to be expressive with my face and gestures.", "category": "responsiveness", "format": "likert"},
            {"id": 23, "text": "I prioritize people's feelings over task completion.", "category": "responsiveness", "format": "likert"},
            {"id": 24, "text": "I am comfortable discussing personal topics.", "category": "responsiveness", "format": "likert"},
            {"id": 25, "text": "I prefer collaborating with others rather than working independently.", "category": "responsiveness", "format": "likert"},
            {"id": 26, "text": "I am sensitive to the moods and emotions of others.", "category": "responsiveness", "format": "likert"},
            {"id": 27, "text": "I enjoy socializing and casual conversation.", "category": "responsiveness", "format": "likert"},
            {"id": 28, "text": "I prefer a supportive environment over a competitive one.", "category": "responsiveness", "format": "likert"},
            {"id": 29, "text": "I am open about sharing my feelings.", "category": "responsiveness", "format": "likert"},
            {"id": 30, "text": "I tend to be informal rather than formal in interactions.", "category": "responsiveness", "format": "likert"}
        ]
        
        assessment = Assessment(
            name="Social Styles Assessment",
            description="This assessment helps identify your social style based on assertiveness and responsiveness dimensions. Rate each statement on a scale of 1-4: 1 = Strongly Disagree, 2 = Somewhat Disagree, 3 = Somewhat Agree, 4 = Strongly Agree.",
            questions=json.dumps(questions)
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        print("Database initialized with updated Social Styles Assessment using Likert scale format.")

if __name__ == "__main__":
    initialize_assessment() 