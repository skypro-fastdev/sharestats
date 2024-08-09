"""Add new achievement types

Revision ID: 762faaf83cfd
Revises: 35c21574baea
Create Date: 2024-08-09 12:42:49.511672

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "762faaf83cfd"
down_revision = "35c21574baea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE achievementtype ADD VALUE IF NOT EXISTS 'CHILLY'")
    op.execute("ALTER TYPE achievementtype ADD VALUE IF NOT EXISTS 'DETERMINED'")
    op.execute("ALTER TYPE achievementtype ADD VALUE IF NOT EXISTS 'LURKY'")
    op.execute("ALTER TYPE achievementtype ADD VALUE IF NOT EXISTS 'LASTMINUTE'")


def downgrade() -> None:
    pass
