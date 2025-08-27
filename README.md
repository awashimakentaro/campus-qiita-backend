# campus-qiita-backend
大学版キータ(FastAPI)の開発

dockerの起動方法
-docker compose up -d これで起動
-docker compose config 構文ミスがないかバリデーション　　configuration(設定) validation(検証)
-docker compose ps 状態確認
-docker compose ps コンテナがちゃんと立ち上がっているのかを一覧で確認
-docker logs -f uniqiita-db　コンテナ内部のログ出力をみるためのもの
-docker exec -it uniqiita-db psql -U postgres -d uni_qiita -c "SELECT version();"　「DBがPostgresの何バージョンで動いてるか」を確認
-docker exec -it uniqiita-db psql -U postgres -d uni_qiita -c "SELECT 1;"  DBが正しく動いてSQLを返せるか」


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