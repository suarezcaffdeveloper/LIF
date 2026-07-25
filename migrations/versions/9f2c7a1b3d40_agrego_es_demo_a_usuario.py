"""agrego es_demo a usuario

Revision ID: 9f2c7a1b3d40
Revises: 7bdb8ecc6d06
Create Date: 2026-07-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f2c7a1b3d40'
down_revision = '7bdb8ecc6d06'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('es_demo', sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade():
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_column('es_demo')
