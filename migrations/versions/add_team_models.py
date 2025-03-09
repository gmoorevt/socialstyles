"""Add team models

Revision ID: add_team_models
Revises: 
Create Date: 2024-03-09 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_team_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create teams table
    op.create_table('teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create team_members table
    op.create_table('team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id', name='unique_team_membership')
    )
    
    # Create team_invites table
    op.create_table('team_invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on token for faster lookups
    op.create_index(op.f('ix_team_invites_token'), 'team_invites', ['token'], unique=True)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_team_invites_token'), table_name='team_invites')
    op.drop_table('team_invites')
    op.drop_table('team_members')
    op.drop_table('teams') 