"""Schemat początkowy: użytkownicy, mieszkania, członkostwa, zaproszenia, typy zadań, zadania i rotacja.

Dodaje też globalne typy zadań (flat_id = NULL), dostępne w każdym mieszkaniu.

Revision ID: 9beffc748319
Revises: 
Create Date: 2026-10-23 18:30:28.671560

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '9beffc748319'
down_revision = None
branch_labels = None
depends_on = None


DEFAULT_TASK_TYPES = [
    {"name": "Sprzątanie", "icon": "bi-stars", "default_points": 10},
    {"name": "Łazienka", "icon": "bi-droplet-half", "default_points": 15},
    {"name": "Kuchnia", "icon": "bi-cup-hot", "default_points": 10},
    {"name": "Śmieci", "icon": "bi-trash3", "default_points": 5},
    {"name": "Zakupy", "icon": "bi-basket2", "default_points": 10},
    {"name": "Pranie", "icon": "bi-water", "default_points": 10},
    {"name": "Inne", "icon": "bi-check2-square", "default_points": 5},
]


def upgrade():
    op.create_table('flats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_flats'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('display_name', sa.String(length=50), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('color_index', sa.SmallInteger(), nullable=False),
    sa.Column('avatar_filename', sa.String(length=64), nullable=True),
    sa.Column('session_token', sa.String(length=64), nullable=False),
    sa.Column('failed_logins', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('color_index BETWEEN 0 AND 11', name=op.f('ck_users_color_index_range')),
    sa.CheckConstraint('failed_logins >= 0', name=op.f('ck_users_failed_logins_non_negative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    sa.UniqueConstraint('session_token', name=op.f('uq_users_session_token'))
    )
    op.create_table('invites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('flat_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_invites_created_by_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['flat_id'], ['flats.id'], name=op.f('fk_invites_flat_id_flats'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invites')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_invites_token_hash'))
    )
    with op.batch_alter_table('invites', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_invites_flat_id'), ['flat_id'], unique=False)

    op.create_table('memberships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('flat_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('admin', 'member', name='member_role', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('status', sa.Enum('pending', 'active', 'rejected', name='membership_status', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['flat_id'], ['flats.id'], name=op.f('fk_memberships_flat_id_flats'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_memberships_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_memberships')),
    sa.UniqueConstraint('user_id', 'flat_id', name=op.f('uq_memberships_user_id_flat_id'))
    )
    with op.batch_alter_table('memberships', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_memberships_flat_id'), ['flat_id'], unique=False)
        batch_op.create_index('uq_memberships_one_admin_per_flat', ['flat_id'], unique=True, postgresql_where=sa.text("role = 'admin'"), sqlite_where=sa.text("role = 'admin'"))

    op.create_table('task_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('flat_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('icon', sa.String(length=40), nullable=False),
    sa.Column('default_points', sa.SmallInteger(), nullable=False),
    sa.CheckConstraint("icon LIKE 'bi-%%'", name=op.f('ck_task_types_icon_bootstrap_class')),
    sa.CheckConstraint('default_points BETWEEN 1 AND 100', name=op.f('ck_task_types_default_points_range')),
    sa.ForeignKeyConstraint(['flat_id'], ['flats.id'], name=op.f('fk_task_types_flat_id_flats'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_task_types')),
    sa.UniqueConstraint('flat_id', 'name', name=op.f('uq_task_types_flat_id_name'))
    )
    with op.batch_alter_table('task_types', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_task_types_flat_id'), ['flat_id'], unique=False)

    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('flat_id', sa.Integer(), nullable=False),
    sa.Column('task_type_id', sa.Integer(), nullable=False),
    sa.Column('assignee_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('parent_task_id', sa.Integer(), nullable=True),
    sa.Column('occurrence_index', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('points', sa.SmallInteger(), nullable=False),
    sa.Column('status', sa.Enum('open', 'done', name='task_status', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('done_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('done_by_id', sa.Integer(), nullable=True),
    sa.Column('recurrence', sa.Enum('none', 'daily', 'weekly', 'monthly', name='task_recurrence', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('assignment_mode', sa.Enum('fixed', 'rotation', 'pool', name='task_assignment_mode', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("(status = 'done') = (done_at IS NOT NULL)", name=op.f('ck_tasks_done_at_matches_status')),
    sa.CheckConstraint("parent_task_id IS NULL OR recurrence = 'none'", name=op.f('ck_tasks_occurrence_not_recurring')),
    sa.CheckConstraint('length(description) <= 1000', name=op.f('ck_tasks_description_length')),
    sa.CheckConstraint('points BETWEEN 1 AND 100', name=op.f('ck_tasks_points_range')),
    sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], name=op.f('fk_tasks_assignee_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_tasks_created_by_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['done_by_id'], ['users.id'], name=op.f('fk_tasks_done_by_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['flat_id'], ['flats.id'], name=op.f('fk_tasks_flat_id_flats'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], name=op.f('fk_tasks_parent_task_id_tasks'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['task_type_id'], ['task_types.id'], name=op.f('fk_tasks_task_type_id_task_types')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tasks')),
    sa.UniqueConstraint('parent_task_id', 'occurrence_index', name=op.f('uq_tasks_parent_task_id_occurrence_index'))
    )
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tasks_assignee_id'), ['assignee_id'], unique=False)
        batch_op.create_index('ix_tasks_flat_id_due_date', ['flat_id', 'due_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_tasks_parent_task_id'), ['parent_task_id'], unique=False)

    op.create_table('rotation_members',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.SmallInteger(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name=op.f('fk_rotation_members_task_id_tasks'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_rotation_members_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rotation_members')),
    sa.UniqueConstraint('task_id', 'user_id', name=op.f('uq_rotation_members_task_id_user_id'))
    )
    with op.batch_alter_table('rotation_members', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rotation_members_user_id'), ['user_id'], unique=False)


    task_types = sa.table(
        "task_types",
        sa.column("flat_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("icon", sa.String),
        sa.column("default_points", sa.SmallInteger),
    )
    op.bulk_insert(task_types, [{"flat_id": None, **row} for row in DEFAULT_TASK_TYPES])


def downgrade():
    with op.batch_alter_table('rotation_members', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rotation_members_user_id'))

    op.drop_table('rotation_members')
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tasks_parent_task_id'))
        batch_op.drop_index('ix_tasks_flat_id_due_date')
        batch_op.drop_index(batch_op.f('ix_tasks_assignee_id'))

    op.drop_table('tasks')
    with op.batch_alter_table('task_types', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_types_flat_id'))

    op.drop_table('task_types')
    with op.batch_alter_table('memberships', schema=None) as batch_op:
        batch_op.drop_index('uq_memberships_one_admin_per_flat', postgresql_where=sa.text("role = 'admin'"), sqlite_where=sa.text("role = 'admin'"))
        batch_op.drop_index(batch_op.f('ix_memberships_flat_id'))

    op.drop_table('memberships')
    with op.batch_alter_table('invites', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_invites_flat_id'))

    op.drop_table('invites')
    op.drop_table('users')
    op.drop_table('flats')
