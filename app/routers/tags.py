# app/routers/tags.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tag import TagCreate, TagOut
from src.models.tag import Tag

router = APIRouter(
    prefix="/v1/tags",
    tags=["tags"],
    redirect_slashes=False,  # ★ / と /なしの自動307を止める
)

# ---------- Create ----------
@router.post("/", response_model=TagOut)
def create_tag(
    tag_in: TagCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(Tag).filter(Tag.name == tag_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(name=tag_in.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

# スラ無しでも作成OK（スキーマ非表示）
@router.post("", response_model=TagOut, include_in_schema=False)
def create_tag_no_slash(
    tag_in: TagCreate,
    db: Session = Depends(get_db),
):
    return create_tag(tag_in=tag_in, db=db)

# ---------- List/Search ----------
@router.get("/", response_model=List[TagOut])
def list_tags(
    query: Optional[str] = Query(None, description="タグ名の部分一致検索"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Tag)
    if query:
        q = q.filter(Tag.name.ilike(f"%{query}%"))
    rows = q.order_by(Tag.created_at.desc()).limit(limit).all()
    return rows

# スラ無しでも一覧OK（スキーマ非表示）
@router.get("", response_model=List[TagOut], include_in_schema=False)
def list_tags_no_slash(
    query: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_tags(query=query, limit=limit, db=db)
