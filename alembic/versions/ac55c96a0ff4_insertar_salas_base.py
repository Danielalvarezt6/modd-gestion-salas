"""insertar salas base

Revision ID: ac55c96a0ff4
Revises: 23c6ec1f1aa0
Create Date: 2026-06-18 02:03:38.553896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac55c96a0ff4'
down_revision: Union[str, None] = '23c6ec1f1aa0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    for numero_sala, capacidad in ((1, 30), (2, 45), (3, 70)):
        connection.execute(
            sa.text(
                """
                INSERT INTO sala (numero_sala, capacidad)
                VALUES (:numero_sala, :capacidad)
                ON CONFLICT (numero_sala) DO NOTHING
                """
            ),
            {"numero_sala": numero_sala, "capacidad": capacidad},
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM sala WHERE numero_sala IN (1, 2, 3)"))
