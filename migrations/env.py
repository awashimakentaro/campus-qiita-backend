import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# --- ① .env を読む（これより前に getenv を呼ばない） ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../backend/migrations
PROJECT_ROOT = os.path.dirname(BASE_DIR)                # .../backend


load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.models import Base
from src.models.user import User       # noqa: F401
from src.models.article import Article # noqa: F401
from src.models.tag import Tag         # noqa: F401
from src.models.article_tag import article_tags  # noqa: F401


# 今後、Tag などを追加したらここに import を足す

# --- ③ Alembic の基本設定 ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- ④ DB URL を Alembic に渡す ---
DATABASE_URL = os.getenv("DATABASE_URL")
print("Alembic connecting to:", DATABASE_URL)
print("DEBUG tables seen by Alembic:", sorted(Base.metadata.tables.keys()))
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# --- ⑤ autogenerate が参照するメタデータ ---
target_metadata = Base.metadata

# --- ⑥ オフライン/オンライン実行関数 ---
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,      # ★必須
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,  # ★必須
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

# --- ⑦ エントリーポイント（最後に置く） ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
