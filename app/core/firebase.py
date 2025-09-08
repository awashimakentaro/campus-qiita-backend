# app/core/firebase.py
import os
import json
from typing import Optional

_FBA_READY = False
firebase_app = None

try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth  # noqa: F401
except Exception:
    # ランタイムに SDK 自体が無い場合
    firebase_admin = None  # type: ignore

def _pick_cred_file(path: str) -> Optional[str]:
    """
    与えられたパスが:
      - ファイル: そのまま返す
      - ディレクトリ: 中の *.json を一つ選んで返す（最初に見つかったもの）
      - それ以外: None
    """
    if not path:
        return None
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path
    if os.path.isdir(path):
        # secrets がディレクトリとしてマウントされるケースに対応
        for name in os.listdir(path):
            if name.lower().endswith(".json"):
                candidate = os.path.join(path, name)
                if os.path.isfile(candidate):
                    return candidate
        return None
    return None

def _resolve_credentials_path() -> Optional[str]:
    """
    優先順で資格情報を解決する:
      1) FIREBASE_CREDENTIALS_FILE（ファイル or ディレクトリ）
      2) GOOGLE_APPLICATION_CREDENTIALS（ファイル想定）
      3) FIREBASE_CREDENTIALS（リポジトリ内の相対パスなど）
    """
    envs = [
        os.getenv("FIREBASE_CREDENTIALS_FILE"),
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        os.getenv("FIREBASE_CREDENTIALS"),
    ]
    for raw in envs:
        if not raw:
            continue
        picked = _pick_cred_file(raw)
        if picked:
            return picked
    return None

def _initialize():
    global _FBA_READY, firebase_app

    if firebase_admin is None:
        _FBA_READY = False
        return

    # 既に初期化済みならスキップ
    try:
        firebase_app = firebase_admin.get_app()
        _FBA_READY = True
        return
    except Exception:
        pass

    cred_path = _resolve_credentials_path()
    if not cred_path:
        # 資格情報が見つからない場合は未初期化のまま
        _FBA_READY = False
        return

    # JSON が壊れていないか軽くチェック（任意）
    try:
        with open(cred_path, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception:
        # 破損していたら諦める
        _FBA_READY = False
        return

    try:
        cred = credentials.Certificate(cred_path)
        # projectId は環境変数があれば使う（無くても JSON から解決される）
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        opts = {"projectId": project_id} if project_id else None
        firebase_app = firebase_admin.initialize_app(cred, opts) if opts else firebase_admin.initialize_app(cred)
        _FBA_READY = True
    except Exception:
        _FBA_READY = False

# モジュール import 時に初期化を試みる
_initialize()

# 外から使うフラグ
FIREBASE_READY = _FBA_READY