# ベースイメージ（Python 3.11）
FROM python:3.11-slim

# 作業ディレクトリ作成
WORKDIR /app

# 依存関係（あれば入れる）
COPY requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi


# 依存関係インストール
RUN pip install --no-cache-dir -r requirements.txt || true

# ソースコードをコピー
COPY . /app

# FastAPIをuvicornで起動する
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
