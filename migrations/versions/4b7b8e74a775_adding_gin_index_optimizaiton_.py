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

def _create_index(table, column):
    col_func = 'lower({})'.format(column)
    # col_func = '{}'.format(column)
    kwargs = {'postgresql_using': 'gin',
              'postgresql_ops': {col_func: 'gin_trgm_ops'}}

    op.create_index(op.f('ix_{}_{}'.format(table, column)), table, [sa.text(col_func)],
                    **kwargs)



def upgrade():
    # def col_fun(column):
    #     'unaccent(lower({}))'.format(column)
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    _create_index('member', 'name')
    _create_index('member', 'phone')
    _create_index('member', 'email')


def downgrade():
    op.drop_index(op.f('ix_member_name'), table_name='member')
    op.drop_index(op.f('ix_member_email'), table_name='member')
    op.drop_index(op.f('ix_member_phone'), table_name='member')

