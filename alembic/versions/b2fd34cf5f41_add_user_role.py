"""add user role

Revision ID: b2fd34cf5f41
Revises: 002869cf0761
Create Date: 2026-05-02 18:26:24.454286

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2fd34cf5f41"
down_revision: Union[str, Sequence[str], None] = "002869cf0761"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role_enum = postgresql.ENUM("USER", "ADMIN", name="userrole")
    user_role_enum.create(op.get_bind())

    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("USER", "ADMIN", name="userrole"),
            nullable=False,
            server_default="USER",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")

    user_role_enum = postgresql.ENUM("USER", "ADMIN", name="userrole")
    user_role_enum.drop(op.get_bind())
