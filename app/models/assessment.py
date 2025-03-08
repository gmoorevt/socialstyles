from datetime import datetime
import json
from app import db

class Assessment(db.Model):
    __tablename__ = 'assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    questions = db.Column(db.Text)  # JSON string of questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with assessment results
    results = db.relationship('AssessmentResult', backref='assessment', lazy='dynamic')
    
    def get_questions(self):
        """Return the questions as a Python object."""
        return json.loads(self.questions)
    
    def __repr__(self):
        return f'<Assessment {self.name}>'

class AssessmentResult(db.Model):
    __tablename__ = 'assessment_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    responses = db.Column(db.Text)  # JSON string of responses
    assertiveness_score = db.Column(db.Float)
    responsiveness_score = db.Column(db.Float)
    social_style = db.Column(db.String(20))  # Driver, Expressive, Amiable, Analytical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_responses(self):
        """Return the responses as a Python object."""
        return json.loads(self.responses)
    
    def set_responses(self, responses_dict):
        """Set the responses from a Python dictionary."""
        self.responses = json.dumps(responses_dict)
    
    def calculate_scores(self):
        """Calculate assertiveness and responsiveness scores based on responses."""
        responses = self.get_responses()
        
        # Calculate assertiveness score (questions 1-15)
        assertiveness_total = sum(responses.get(str(i), 0) for i in range(1, 16))
        self.assertiveness_score = assertiveness_total / 15
        
        # Calculate responsiveness score (questions 16-30)
        responsiveness_total = sum(responses.get(str(i), 0) for i in range(16, 31))
        self.responsiveness_score = responsiveness_total / 15
        
        # Determine social style based on scores
        self.determine_social_style()
        
        return self.assertiveness_score, self.responsiveness_score
    
    def determine_social_style(self):
        """Determine the social style based on assertiveness and responsiveness scores."""
        # Using 2.5 as the cutoff point (midpoint of 1-4 scale)
        if self.assertiveness_score >= 2.5 and self.responsiveness_score >= 2.5:
            self.social_style = "EXPRESSIVE"
        elif self.assertiveness_score >= 2.5 and self.responsiveness_score < 2.5:
            self.social_style = "DRIVER"
        elif self.assertiveness_score < 2.5 and self.responsiveness_score >= 2.5:
            self.social_style = "AMIABLE"
        else:  # assertiveness < 2.5 and responsiveness < 2.5
            self.social_style = "ANALYTICAL"
        
        return self.social_style
    
    def __repr__(self):
        return f'<AssessmentResult {self.id} - User {self.user_id}>' 