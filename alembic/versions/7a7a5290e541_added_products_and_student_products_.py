"""Added products and student_products table

Revision ID: 7a7a5290e541
Revises: 4cdc808942d7
Create Date: 2024-08-23 10:42:53.424555

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a7a5290e541'
down_revision = '4cdc808942d7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('products',
    sa.Column('id', sqlmodel.AutoString(), nullable=False),
    sa.Column('title', sqlmodel.AutoString(), nullable=False),
    sa.Column('value', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sqlmodel.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_products_created_at'), 'student_products', ['created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_student_products_created_at'), table_name='student_products')
    op.drop_table('student_products')
    op.drop_table('products')
    # ### end Alembic commands ###