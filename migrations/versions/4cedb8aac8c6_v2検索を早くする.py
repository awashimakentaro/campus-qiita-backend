from alembic import op

# revision identifiers, used by Alembic.
revision = "add_trgm_idx_articles"
down_revision = "dcea8460b3e9"
branch_labels = None
depends_on = None

def upgrade():
    # 1) 拡張を有効化（存在しなければ）
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2) タイトルと本文にトライグラムGINインデックス
    #    ILIKE '%query%' を高速化
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_articles_title_trgm
        ON articles
        USING gin (title gin_trgm_ops);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_articles_body_md_trgm
        ON articles
        USING gin (body_md gin_trgm_ops);
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_articles_body_md_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_articles_title_trgm;")
    # 拡張は共有資産なので基本は落とさない（必要なら↓を有効化）
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm;")