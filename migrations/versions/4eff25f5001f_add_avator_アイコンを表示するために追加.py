"""add avatar アイコンを表示するために追加

Revision ID: 4eff25f5001f
Revises: add_trgm_idx_articles
Create Date: 2025-09-07 11:48:41.273444+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4eff25f5001f"
down_revision: Union[str, Sequence[str], None] = "add_trgm_idx_articles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 既存のインデックス削除（既に削除済みならスキップされる）え
    try:
        op.drop_index(op.f("ix_articles_body_md_trgm"), table_name="articles")
    except Exception:
        pass
    try:
        op.drop_index(op.f("ix_articles_title_trgm"), table_name="articles")
    except Exception:
        pass

    # UNIQUE 制約を追加（存在しなければ）
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_like_article_user'
            ) THEN
                ALTER TABLE likes
                ADD CONSTRAINT uq_like_article_user UNIQUE (article_id, user_id);
            END IF;
        END
        $$;
        """
    )

    # avatar カラム追加（存在しなければ）
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("avatar", sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""

    # avatar カラム削除
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("avatar")

    # UNIQUE 制約削除（存在すれば）
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_like_article_user'
            ) THEN
                ALTER TABLE likes
                DROP CONSTRAINT uq_like_article_user;
            END IF;
        END
        $$;
        """
    )

    # インデックスを元に戻す
    op.create_index(
        op.f("ix_articles_title_trgm"),
        "articles",
        ["title"],
        unique=False,
        postgresql_ops={"title": "gin_trgm_ops"},
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_articles_body_md_trgm"),
        "articles",
        ["body_md"],
        unique=False,
        postgresql_ops={"body_md": "gin_trgm_ops"},
        postgresql_using="gin",
    )