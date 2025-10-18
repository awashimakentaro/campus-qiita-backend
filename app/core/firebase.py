# app/core/firebase.py
import os
import json
import base64
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

_FBA_READY = False
firebase_app = None

try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth  # noqa: F401
except Exception:
    # ランタイムに SDK 自体が無い場合
    firebase_admin = None  # type: ignore


def _pick_cred_file(path: str) -> Optional[str]:
    """Return a credential file path when the input is a file or directory."""
    if not path:
        return None
    path = path.strip()
    if not path:
        return None
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path
    if os.path.isdir(path):
        for name in os.listdir(path):
            if name.lower().endswith('.json'):
                candidate = os.path.join(path, name)
                if os.path.isfile(candidate):
                    return candidate
        return None
    return None


DEFAULT_CREDENTIAL_PATHS = (
    './secrets/firebase-adminsdk.json',
    '/secrets/firebase-adminsdk.json',
)

def _resolve_credentials_path() -> Optional[str]:
    candidates = [
        os.getenv('FIREBASE_CREDENTIALS_FILE'),
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        os.getenv('FIREBASE_CREDENTIALS'),
        *DEFAULT_CREDENTIAL_PATHS,
    ]
    for raw in candidates:
        if not raw:
            continue
        raw = raw.strip()
        if not raw:
            continue
        picked = _pick_cred_file(raw)
        if picked:
            logger.info('Firebase credentials file resolved: %s', picked)
            return picked
        logger.warning('Firebase credentials path not usable: %s', raw)
    return None


def _try_parse_json(raw: str) -> Optional[Dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            decoded = base64.b64decode(raw)
        except Exception:
            return None
        try:
            return json.loads(decoded.decode('utf-8'))
        except Exception:
            return None


def _resolve_inline_credentials() -> Optional[Dict[str, Any]]:
    candidates = [
        ("FIREBASE_SERVICE_ACCOUNT_JSON", os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')),
        ("FIREBASE_SERVICE_ACCOUNT", os.getenv('FIREBASE_SERVICE_ACCOUNT')),
        ("FIREBASE_ADMIN_CREDENTIAL_JSON", os.getenv('FIREBASE_ADMIN_CREDENTIAL_JSON')),
    ]
    for name, raw in candidates:
        if not raw:
            continue
        raw = raw.strip()
        if not raw:
            continue
        parsed = _try_parse_json(raw)
        if parsed:
            logger.info("Firebase inline credentials resolved from %s", name)
            return parsed
        logger.warning("Firebase inline credentials invalid in %s", name)
    return None


def _resolve_credentials_source() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    path = _resolve_credentials_path()
    if path:
        return path, None
    inline = _resolve_inline_credentials()
    if inline:
        return None, inline
    return None, None


def _initialize(force: bool = False) -> None:
    global _FBA_READY, firebase_app

    if firebase_admin is None:
        _FBA_READY = False
        return

    if not force:
        try:
            firebase_app = firebase_admin.get_app()
            _FBA_READY = True
            return
        except Exception:
            pass

    cred_path, cred_inline = _resolve_credentials_source()
    if not cred_path and cred_inline is None:
        logger.error('Firebase credentials not found in environment')
        _FBA_READY = False
        return

    source: Any
    if cred_path:
        try:
            with open(cred_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except Exception:
            logger.exception('Failed to read Firebase credential file: %s', cred_path)
            _FBA_READY = False
            return
        source = cred_path
        os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', cred_path)
    else:
        source = cred_inline

    try:
        cred = credentials.Certificate(source)
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        opts = {'projectId': project_id} if project_id else None
        firebase_app = firebase_admin.initialize_app(cred, opts) if opts else firebase_admin.initialize_app(cred)
        _FBA_READY = True
        logger.info('Firebase Admin SDK initialized successfully')
    except Exception:
        logger.exception('Failed to initialize Firebase Admin SDK')
        _FBA_READY = False


def ensure_firebase_ready() -> bool:
    global _FBA_READY, FIREBASE_READY
    if _FBA_READY:
        return True
    _initialize(force=True)
    FIREBASE_READY = _FBA_READY
    return _FBA_READY


_initialize()
FIREBASE_READY = _FBA_READY

__all__ = ['firebase_app', 'firebase_auth', 'FIREBASE_READY', 'ensure_firebase_ready']
