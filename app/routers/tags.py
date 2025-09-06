from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.tag import TagCreate, TagOut
from src.models.tag import Tag

router = APIRouter(
    prefix="/v1/tags",
    tags=["tags"],
)

# タグ作成エラー解消
@router.post("/", response_model=TagOut)
def create_tag(tag_in: TagCreate, db: Session = Depends(get_db)):
    existing = db.query(Tag).filter(Tag.name == tag_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(name=tag_in.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

# タグ検索
@router.get("/", response_model=List[TagOut])
def list_tags(
    query: str = Query("", description="タグ名の部分一致検索"),
    db: Session = Depends(get_db),
):
    q = db.query(Tag)
    if query:
        q = q.filter(Tag.name.ilike(f"%{query}%"))
    return q.all()