"""Add is_anonymous_assessment field to User model

Revision ID: 5011a7c2443a
Revises: f903bb3846e1
Create Date: 2025-03-13 14:33:56.056397

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5011a7c2443a'
down_revision = 'f903bb3846e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_anonymous_assessment', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_anonymous_assessment')

    # ### end Alembic commands ###
