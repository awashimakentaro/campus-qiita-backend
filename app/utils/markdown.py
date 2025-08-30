from markdown import markdown as md_to_html
import bleach

# 許可タグ
ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union({
    "p", "pre", "code", "blockquote", "hr", "br",
    "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "th", "td",
    "em", "strong", "a"
})

# 許可属性
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
}

def render_and_sanitize(markdown_text: str) -> str:
    """
    Markdown → HTML 変換後、サニタイズして返す。
    """
    # MarkdownをHTMLへ
    html = md_to_html(
        markdown_text or "",
        extensions=["extra", "sane_lists", "toc"]
    )

    # 危険なタグを除去
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,
    )

    # 自動リンク化　bleach ライブラリ 変換後のHTMLから危険なタグや属性を除去するため。
    linked = bleach.linkify(
        cleaned,
        skip_tags=["pre", "code"],
    )
    return linked

#    何のための作業？
#	簡単にいうと、ユーザーが入力したmarkdownを安全なhtmlに変換してdbに保存するための変換エンジンを作った
#CRUD create read update deleate     
#xss攻撃　誰かがコメント欄に alert("あなたのCookieは盗まれました！");　みたいにつつtp他の人に影響が出たりする
#サニタイズ　入力データを安全に加工して、危険な部分を除去すること。
#記事作成APIや編集APIなどで使う。これから他の機能もこれのような感じで使いたいのなら、この関数を再利用できるからutilsに書き出している