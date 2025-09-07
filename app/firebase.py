# app/firebase.py
import os
import firebase_admin
from firebase_admin import credentials, auth

# すでに初期化されている場合はスキップ
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
    firebase_admin.initialize_app(cred)

# 他のファイルから import して auth を使えるようにする
firebase_auth = auth