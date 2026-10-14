"""Create price history table."""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_prices"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_prices_ticker_timestamp", "prices", ["ticker", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_prices_ticker_timestamp", table_name="prices")
    op.drop_table("prices")
