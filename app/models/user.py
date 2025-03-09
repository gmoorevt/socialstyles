from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from time import time
import jwt

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)  # Track last login time
    is_admin = db.Column(db.Boolean, default=False)  # Admin flag
    
    # Relationship with assessment results
    assessment_results = db.relationship('AssessmentResult', backref='user', lazy='dynamic')
    
    # Team relationships
    owned_teams = db.relationship('Team', foreign_keys='Team.owner_id', 
                                 backref=db.backref('owner_relation', uselist=False),
                                 lazy='dynamic', cascade='all, delete-orphan')
    team_memberships = db.relationship('TeamMember', backref='user', lazy='dynamic', 
                                      cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login time."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def generate_reset_token(self, expires_in=3600):
        """Generate a token for password reset that expires in 1 hour."""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_token(token):
        """Verify the reset token."""
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def get_teams(self):
        """Get all teams the user is a member of."""
        from app.models.team import Team, TeamMember
        team_ids = db.session.query(TeamMember.team_id).filter_by(user_id=self.id).all()
        return Team.query.filter(Team.id.in_([t[0] for t in team_ids])).all()
    
    def get_latest_assessment_result(self):
        """Get the user's most recent assessment result."""
        return self.assessment_results.order_by(db.desc('created_at')).first()
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 