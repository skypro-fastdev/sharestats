"""Initial migration

Revision ID: 35c21574baea
Revises:
Create Date: 2024-07-30 23:19:42.642388

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "35c21574baea"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.AutoString(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "NEWBIE",
                "POPCORN",
                "NIGHT_OWL",
                "SUNSHINE",
                "NO_REST",
                "LIGHTNING",
                "FLAWLESS",
                "LIVEWATCHER",
                "QUESTIONCAT",
                "RESPONSIVE",
                "SHERIFF",
                "PERSONAL",
                name="achievementtype",
            ),
            nullable=False,
        ),
        sa.Column("description", sqlmodel.AutoString(), nullable=False),
        sa.Column("profession", sqlmodel.AutoString(), nullable=False),
        sa.Column("picture", sqlmodel.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", "profession"),
    )
    op.create_index(op.f("ix_achievements_profession"), "achievements", ["profession"], unique=False)
    op.create_index(op.f("ix_achievements_title"), "achievements", ["title"], unique=False)
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sqlmodel.AutoString(), nullable=True),
        sa.Column("last_name", sqlmodel.AutoString(), nullable=True),
        sa.Column(
            "profession",
            sa.Enum("PD", "DA", "GD", "WD", "QA", "JD", "IM", "PM", "NA", name="professionenum"),
            nullable=False,
        ),
        sa.Column("started_at", sa.Date(), nullable=False),
        sa.Column("statistics", sqlmodel.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "student_achievements",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievements.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("student_id", "achievement_id"),
    )
    op.create_index(op.f("ix_student_achievements_created_at"), "student_achievements", ["created_at"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_student_achievements_created_at"), table_name="student_achievements")
    op.drop_table("student_achievements")
    op.drop_table("students")
    op.drop_index(op.f("ix_achievements_title"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_profession"), table_name="achievements")
    op.drop_table("achievements")
    # ### end Alembic commands ###
