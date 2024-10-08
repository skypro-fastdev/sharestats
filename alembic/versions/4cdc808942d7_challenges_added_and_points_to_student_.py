"""Challenges added and points to Student model

Revision ID: 4cdc808942d7
Revises: 762faaf83cfd
Create Date: 2024-08-20 10:25:07.396271

"""

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision = "4cdc808942d7"
down_revision = "762faaf83cfd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "challenges",
        sa.Column("id", sqlmodel.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.AutoString(), nullable=False),
        sa.Column("eval", sqlmodel.AutoString(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "student_challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("challenge_id", sqlmodel.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("students", sa.Column("points", sa.Integer(), nullable=True))

    op.execute("UPDATE students SET points = 0 WHERE points IS NULL")

    op.alter_column("students", "points", nullable=False, server_default=sa.text("0::integer"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("students", "points")
    op.drop_table("student_challenges")
    op.drop_table("challenges")
    # ### end Alembic commands ###
