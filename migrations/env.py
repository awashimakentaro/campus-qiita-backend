import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

# --- ここ重要 ---
config = context.config  # これが無いと NameError

# .env から DB URL を読む
load_dotenv()
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# SQLAlchemy のメタデータを Alembic に教える
from src.models import Base
from src.models import user, article  # モデルを import しておく（autogenerate 用）
target_metadata = Base.metadata
# --- ここまで ---
