"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE TYPE user_role AS ENUM ('manager', 'head', 'analyst', 'admin');")
    op.execute("CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high');")
    op.execute("CREATE TYPE request_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'paid');")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Enum("manager", "head", "analyst", "admin", name="user_role", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "wallet_checks",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("risk_level", sa.Enum("low", "medium", "high", name="risk_level", create_type=False), nullable=False),
        sa.Column("categories_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("raw_report_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("checked_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_wallet_checks_risk_score"),
    )

    op.create_table(
        "payment_requests",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("request_no", sa.Text(), nullable=False, unique=True),
        sa.Column("creator_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("network", sa.Text(), nullable=False),
        sa.Column("asset", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(36, 18), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("attachment_url", sa.Text(), nullable=True),
        sa.Column("aml_check_id", sa.UUID(), sa.ForeignKey("wallet_checks.id"), nullable=False),
        sa.Column("status", sa.Enum("draft", "pending", "approved", "rejected", "paid", name="request_status", create_type=False), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("approved_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("tx_hash", sa.Text(), nullable=True, unique=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0", name="ck_payment_requests_amount"),
    )

    op.create_table(
        "status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.UUID(), sa.ForeignKey("payment_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", sa.Enum("draft", "pending", "approved", "rejected", "paid", name="request_status", create_type=False), nullable=True),
        sa.Column("new_status", sa.Enum("draft", "pending", "approved", "rejected", "paid", name="request_status", create_type=False), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("idx_payment_requests_status", "payment_requests", ["status"])
    op.create_index("idx_payment_requests_creator", "payment_requests", ["creator_id"])
    op.create_index("idx_wallet_checks_address_network", "wallet_checks", ["address", "network"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_status_history_request_id", "status_history", ["request_id"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_payment_requests_updated_at
        BEFORE UPDATE ON payment_requests
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_payment_requests_updated_at ON payment_requests;")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at;")

    op.drop_index("idx_status_history_request_id", table_name="status_history")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_wallet_checks_address_network", table_name="wallet_checks")
    op.drop_index("idx_payment_requests_creator", table_name="payment_requests")
    op.drop_index("idx_payment_requests_status", table_name="payment_requests")

    op.drop_table("audit_logs")
    op.drop_table("status_history")
    op.drop_table("payment_requests")
    op.drop_table("wallet_checks")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS request_status;")
    op.execute("DROP TYPE IF EXISTS risk_level;")
    op.execute("DROP TYPE IF EXISTS user_role;")
