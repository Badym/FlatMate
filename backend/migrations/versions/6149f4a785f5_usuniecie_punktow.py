"""Usunięcie punktów: kolumny tasks.points i task_types.default_points.

Punkty nie są częścią aplikacji (decyzja D-31). Ograniczenia zakresu na tych
kolumnach PostgreSQL usuwa razem z kolumnami. Cofnięcie migracji przywraca
kolumny z wartością 10 i ograniczenia 1–100; wcześniejsze wartości nie wracają.

Revision ID: 6149f4a785f5
Revises: 9beffc748319
Create Date: 2026-10-28 18:14:31.320103

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '6149f4a785f5'
down_revision = '9beffc748319'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task_types', schema=None) as batch_op:
        batch_op.drop_column('default_points')

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_column('points')


def downgrade():
    # Wartość domyślna w bazie tylko na czas dodania kolumn do istniejących wierszy.
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('points', sa.SmallInteger(), nullable=False, server_default='10'))
        batch_op.create_check_constraint(op.f('ck_tasks_points_range'), 'points BETWEEN 1 AND 100')
        batch_op.alter_column('points', server_default=None)

    with op.batch_alter_table('task_types', schema=None) as batch_op:
        batch_op.add_column(sa.Column('default_points', sa.SmallInteger(), nullable=False, server_default='10'))
        batch_op.create_check_constraint(
            op.f('ck_task_types_default_points_range'), 'default_points BETWEEN 1 AND 100'
        )
        batch_op.alter_column('default_points', server_default=None)
