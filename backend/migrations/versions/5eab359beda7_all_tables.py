"""all tables

Revision ID: 5eab359beda7
Revises: 
Create Date: 2022-12-10 13:56:58.427263

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5eab359beda7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('position',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('project',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.Column('category', sa.String(length=60), nullable=True),
    sa.Column('descr', sa.String(length=140), nullable=True),
    sa.Column('skill_level', sa.String(length=20), nullable=True),
    sa.Column('setting', sa.String(length=20), nullable=True),
    sa.Column('team_size', sa.String(length=20), nullable=True),
    sa.Column('chat_link', sa.String(length=512), nullable=True),
    sa.Column('language', sa.String(length=5), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_project_timestamp'), ['timestamp'], unique=False)

    op.create_table('rank',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=25), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('rank', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rank_default'), ['default'], unique=False)

    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=25), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_role_default'), ['default'], unique=False)

    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('business',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sub_category', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('community',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sub_category', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('data_science',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sub_category', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('engineering',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sub_category', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('entertainment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sub_category', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('learning',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pace', sa.String(length=60), nullable=True),
    sa.Column('learning_category', sa.String(length=60), nullable=True),
    sa.Column('subject', sa.String(length=60), nullable=True),
    sa.Column('resource', sa.String(length=70), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('position_map',
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('position_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['position_id'], ['position.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], )
    )
    op.create_table('project_tag_map',
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], )
    )
    op.create_table('research',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('field', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('software_dev',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sub_category', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('last_notif_read_time', sa.DateTime(), nullable=True),
    sa.Column('token', sa.String(length=32), nullable=True),
    sa.Column('token_expiration', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_token'), ['token'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    op.create_table('join_requests',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=15), nullable=True),
    sa.Column('msg', sa.String(length=650), nullable=True),
    sa.Column('status', sa.String(length=15), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'project_id')
    )
    with op.batch_alter_table('join_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_join_requests_timestamp'), ['timestamp'], unique=False)

    op.create_table('proj_members',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('rank_id', sa.Integer(), nullable=True),
    sa.Column('position_id', sa.Integer(), nullable=True),
    sa.Column('date_added', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['position_id'], ['position.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['rank_id'], ['rank.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'project_id')
    )
    op.create_table('project_creator_map',
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('resource',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.Column('category', sa.String(length=60), nullable=True),
    sa.Column('descr', sa.String(length=140), nullable=True),
    sa.Column('link', sa.String(length=512), nullable=True),
    sa.Column('language', sa.String(length=5), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('accepted', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('resource', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_resource_timestamp'), ['timestamp'], unique=False)

    op.create_table('scrum_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('task_type', sa.String(length=15), nullable=True),
    sa.Column('text', sa.String(length=650), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('scrum_tasks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_scrum_tasks_timestamp'), ['timestamp'], unique=False)

    op.create_table('user_tag_map',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('resource_tag_map',
    sa.Column('resource_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['resource_id'], ['resource.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('resource_tag_map')
    op.drop_table('user_tag_map')
    with op.batch_alter_table('scrum_tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_scrum_tasks_timestamp'))

    op.drop_table('scrum_tasks')
    with op.batch_alter_table('resource', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_resource_timestamp'))

    op.drop_table('resource')
    op.drop_table('project_creator_map')
    op.drop_table('proj_members')
    with op.batch_alter_table('join_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_join_requests_timestamp'))

    op.drop_table('join_requests')
    op.drop_table('followers')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_token'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    op.drop_table('software_dev')
    op.drop_table('research')
    op.drop_table('project_tag_map')
    op.drop_table('position_map')
    op.drop_table('learning')
    op.drop_table('entertainment')
    op.drop_table('engineering')
    op.drop_table('data_science')
    op.drop_table('community')
    op.drop_table('business')
    op.drop_table('tag')
    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_role_default'))

    op.drop_table('role')
    with op.batch_alter_table('rank', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rank_default'))

    op.drop_table('rank')
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_project_timestamp'))

    op.drop_table('project')
    op.drop_table('position')
    # ### end Alembic commands ###
