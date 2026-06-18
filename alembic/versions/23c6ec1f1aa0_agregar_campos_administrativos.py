"""agregar campos administrativos

Revision ID: 23c6ec1f1aa0
Revises: d8e1c16088f4
Create Date: 2026-06-18 01:57:52.877830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23c6ec1f1aa0'
down_revision: Union[str, None] = 'd8e1c16088f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("solicitante", "institucion"):
        op.add_column(
            "solicitante",
            sa.Column(
                "institucion",
                sa.String(),
                nullable=True,
                server_default="Universidad de Sonora",
            ),
        )

    if not _has_column("evento", "tipo"):
        op.add_column(
            "evento",
            sa.Column("tipo", sa.String(), nullable=True, server_default="clase"),
        )

    if not _has_column("evento", "estado_evento"):
        op.add_column(
            "evento",
            sa.Column(
                "estado_evento",
                sa.String(),
                nullable=True,
                server_default="confirmado",
            ),
        )


def downgrade() -> None:
    if _has_column("evento", "estado_evento"):
        op.drop_column("evento", "estado_evento")

    if _has_column("evento", "tipo"):
        op.drop_column("evento", "tipo")

    if _has_column("solicitante", "institucion"):
        op.drop_column("solicitante", "institucion")
