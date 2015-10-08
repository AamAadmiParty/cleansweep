"""Adding gin index optimizaiton for autocomplete

Revision ID: 4b7b8e74a775
Revises: cb4ac67bb2b
Create Date: 2015-10-08 05:27:42.804348

"""

# revision identifiers, used by Alembic.
revision = '4b7b8e74a775'
down_revision = 'cb4ac67bb2b'

from alembic import op
import sqlalchemy as sa
connection = op.get_bind()



def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.create_index(op.f('ix_member_name'), 'member', ['name'], postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_index(op.f('ix_member_email'), 'member', ['email'], postgresql_using='gin', postgresql_ops={'email': 'gin_trgm_ops'})
    op.create_index(op.f('ix_member_phone'), 'member', ['phone'], postgresql_using='gin', postgresql_ops={'phone': 'gin_trgm_ops'})


def downgrade():
    op.drop_index(op.f('ix_member_name'), table_name='member')
    op.drop_index(op.f('ix_member_email'), table_name='member')
    op.drop_index(op.f('ix_member_phone'), table_name='member')

