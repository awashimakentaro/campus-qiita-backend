# campus-qiita-backend
Readmeの書き方
https://qiita.com/shun198/items/c983c713452c041ef787
jetとは　https://qiita.com/arara4510/items/55fc005f8f676f40afcb

大学版キータ(FastAPI)の開発

dockerの起動方法
-docker compose up -d これで起動
-docker compose config 構文ミスがないかバリデーション　　configuration(設定) validation(検証)
-docker compose ps 状態確認
-docker compose ps コンテナがちゃんと立ち上がっているのかを一覧で確認
-docker logs -f uniqiita-db　コンテナ内部のログ出力をみるためのもの
-docker exec -it uniqiita-db psql -U postgres -d uni_qiita -c "SELECT version();"　「DBがPostgresの何バージョンで動いてるか」を確認
-docker exec -it uniqiita-db psql -U postgres -d uni_qiita -c "SELECT 1;"  DBが正しく動いてSQLを返せるか」

dockerデスクトップのexecではpsql -U postgres -d uni_qiita　と打つとそこでsqlのコマンドを打てる
`メモ`
docker exec -it uniqiita-db psql -U postgres -d uni_qiita -c "..."
   


docker exec
→ すでに起動しているコンテナの中でコマンドを実行する。

-it
→ -i = 標準入力を有効にする (interactive)。
-t = 疑似端末(TTY)を割り当てる。
両方合わせると「コンテナ内で対話的にコマンドが打てる状態」になる。

uniqiita-db
→ コマンドを実行する対象のコンテナ名（docker-compose.ymlで指定した container_name）。

psql
→ Postgresのクライアント。SQLを実行するためのコマンドラインツール。

-U postgres
→ 接続ユーザー名。ここではユーザーpostgresとしてログイン。

-d uni_qiita
→ 接続するデータベース名。ここでは uni_qiita に接続。

-c "..."
→ -c オプションは「SQL文を1回だけ実行して終了する」という意味。
"..." の中に書いたSQLをそのまま投げる。

dbdiagramからGitHubに載せる最短手順

dbdiagramで Export → DBML（erd.dbml）

Export → PNG/SVG（erd.png or erd.svg）

リポジトリに /docs/db/ フォルダを作って両方配置

README.md に画像を貼る（差分が見やすい）

## ERD
![ERD](docs/db/erd.png)


app/FastAPI アプリのエントリや ルーター / スキーマ / 依存関係 など
 ├── main.py            # FastAPIエントリ
 ├── routers/           # APIルーター (articles.py, users.py ...)
 ├── schemas/           # Pydanticスキーマ
 ├── utils/             # 共通処理
 └── deps.py            # 依存関係 (DBセッション取得など)

 src/ 	•	ドメインロジック（ビジネスロジック）やDBモデルを置く。
 ├── models/            # SQLAlchemyモデル (article.py, user.py ...)
 ├── services/          # ドメインロジック (記事投稿処理, 人気順スコア計算...)
 └── repositories/      # DBアクセス層 (クエリ操作をまとめる)



SELECT <取り出したいカラム>
FROM <どのテーブルから>
WHERE <条件>
ORDER BY <並び順>
LIMIT <何件取るか>;


postgresql+psycopg://postgres:postgres@db:5432/uni_qiita
これは PostgreSQL に接続するための URL（接続文字列）です。アプリ（FastAPI + SQLAlchemy）が DB に繋ぐときに使ってるやつ。
	postgresql+psycopg
→ DBの種類とドライバ
	•	postgresql = PostgreSQL を使う
	•	+psycopg = Python 用のドライバ（psycopg3）を経由する
	•	postgres:postgres
→ ユーザー名:パスワード
	•	ユーザー: postgres
	•	パスワード: postgres
	•	@db:5432
→ ホスト名とポート
	•	ホスト: db （docker-compose 内でDBコンテナに付けたサービス名）
	•	ポート: 5432（Postgresのデフォルトポート）
	•	/uni_qiita
→ 接続するデータベース
	•	今回は uni_qiita というDBを使う

 "insert into article_tags (article_id, tag_id) values (2, 1) on conflict do nothing;"

git reset --hard origin/main でlocalをリモートの状態にする
git clean -fd　とすることで余分なフォルダを消す