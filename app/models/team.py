from datetime import datetime, timedelta
import uuid
from app import db
from flask import url_for

# Association table for team memberships
class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'owner' or 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure no duplicate memberships for the same team and user
    __table_args__ = (db.UniqueConstraint('team_id', 'user_id', name='unique_team_membership'),)
    
    def __repr__(self):
        return f'<TeamMember {self.user_id} in Team {self.team_id}>'

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    invites = db.relationship('TeamInvite', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def owner(self):
        """Get the team owner"""
        from app.models.user import User
        return User.query.get(self.owner_id)
    
    def is_member(self, user):
        """Check if a user is a member of the team"""
        return TeamMember.query.filter_by(team_id=self.id, user_id=user.id).first() is not None
    
    def is_owner(self, user):
        """Check if a user is the owner of the team"""
        return self.owner_id == user.id
    
    def add_member(self, user, role='member'):
        """Add a user to the team"""
        if not self.is_member(user):
            membership = TeamMember(team_id=self.id, user_id=user.id, role=role)
            db.session.add(membership)
            return membership
        return None
    
    def remove_member(self, user):
        """Remove a user from the team"""
        membership = TeamMember.query.filter_by(team_id=self.id, user_id=user.id).first()
        if membership:
            db.session.delete(membership)
            return True
        return False
    
    def get_join_url(self):
        """Get the URL for joining this team"""
        return url_for('team.join', token=self.generate_join_token(), _external=True)
    
    def generate_join_token(self):
        """Generate a token for joining the team"""
        # Simple UUID-based token, could be enhanced with JWT if needed
        return str(uuid.uuid4())
    
    def __repr__(self):
        return f'<Team {self.name}>'

class TeamInvite(db.Model):
    __tablename__ = 'team_invites'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected', 'expired'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(TeamInvite, self).__init__(**kwargs)
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.expires_at:
            # Default expiration: 7 days from creation
            self.expires_at = datetime.utcnow() + timedelta(days=7)
    
    @property
    def is_expired(self):
        """Check if the invitation has expired"""
        return datetime.utcnow() > self.expires_at
    
    def accept(self, user):
        """Accept the invitation and add the user to the team"""
        if self.status == 'pending' and not self.is_expired:
            team = Team.query.get(self.team_id)
            membership = team.add_member(user)
            if membership:
                self.status = 'accepted'
                return True
        return False
    
    def reject(self):
        """Reject the invitation"""
        if self.status == 'pending':
            self.status = 'rejected'
            return True
        return False
    
    def __repr__(self):
        return f'<TeamInvite {self.email} for Team {self.team_id}>' 