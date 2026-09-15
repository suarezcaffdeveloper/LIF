"""agrego captura_jornada

Revision ID: bd830671e5da
Revises: 9f2c7a1b3d40
Create Date: 2026-09-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd830671e5da'
down_revision = '9f2c7a1b3d40'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'captura_jornada',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('temporada_id', sa.Integer(), nullable=False),
        sa.Column('bloque', sa.String(length=20), nullable=False),
        sa.Column('categoria', sa.String(length=50), nullable=False),
        sa.Column('jornada', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=30), nullable=False),
        sa.Column('cloudinary_url', sa.String(length=500), nullable=False),
        sa.Column('cloudinary_public_id', sa.String(length=300), nullable=False),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['temporada_id'], ['temporada.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'temporada_id', 'categoria', 'jornada', 'tipo',
            name='uq_captura_temporada_categoria_jornada_tipo'
        ),
    )


def downgrade():
    op.drop_table('captura_jornada')
