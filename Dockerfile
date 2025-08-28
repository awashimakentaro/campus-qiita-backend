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


#何をする？
#
#Python入りのベースイメージを取ってくる
#
#作業ディレクトリを /app に設定
#
#依存関係をインストール（requirements.txt）
#
#プロジェクトのコードをコピー
#
#コンテナ起動時のコマンド（uvicorn）を指定
#
#これで「アプリが動く箱（イメージ）」が作られる。
#「Dockerfileはコンテナのレシピ」
#Dockerfile と docker-compose.yml の違い
#
#Dockerfile
#
#1つのコンテナの作り方（設計図）を書く
#
#「Pythonを入れる → 必要なライブラリを入れる → uvicornを起動」といった1つの箱のレシピ
#
#例: backend 用の Dockerfile
#
#docker-compose.yml
#
#複数のコンテナをどう組み合わせるかを書く
#
#「db（Postgres）と backend（FastAPI）を一緒に立ち上げて連携させる」といった全体のシナリオ
#
#👉 覚え方：「Dockerfile = 箱の作り方」「docker-compose.yml = 箱の組み合わせ方」