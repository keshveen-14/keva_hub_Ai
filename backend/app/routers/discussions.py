from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/discussions", tags=["Discussions"])


def _serialize(db: Session, d: models.Discussion, current_user: models.Employee) -> schemas.DiscussionOut:
    liked = db.query(models.Like).filter(
        models.Like.discussion_id == d.id, models.Like.employee_id == current_user.id
    ).first() is not None
    return schemas.DiscussionOut(
        id=d.id, title=d.title, content=d.content, image_url=d.image_url,
        author_id=d.author_id, author_name=d.author.name if d.author else None,
        department_id=d.department_id, likes_count=d.likes_count,
        comments_count=len(d.comments), liked_by_me=liked, created_at=d.created_at,
    )


@router.get("", response_model=List[schemas.DiscussionOut])
def list_discussions(
    department_id: Optional[int] = None,
    sort: str = "latest",  # latest | trending | most_liked
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    query = db.query(models.Discussion)
    if department_id:
        query = query.filter(models.Discussion.department_id == department_id)

    items = query.all()
    if sort == "most_liked":
        items.sort(key=lambda d: d.likes_count, reverse=True)
    elif sort == "trending":
        items.sort(key=lambda d: (d.likes_count + len(d.comments)), reverse=True)
    else:
        items.sort(key=lambda d: d.created_at, reverse=True)

    return [_serialize(db, d, current_user) for d in items]


@router.get("/{discussion_id}", response_model=schemas.DiscussionOut)
def get_discussion(discussion_id: int, db: Session = Depends(get_db),
                    current_user: models.Employee = Depends(get_current_user)):
    d = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return _serialize(db, d, current_user)


@router.post("", response_model=schemas.DiscussionOut)
def create_discussion(payload: schemas.DiscussionCreate, db: Session = Depends(get_db),
                       current_user: models.Employee = Depends(get_current_user)):
    d = models.Discussion(
        title=payload.title, content=payload.content, image_url=payload.image_url,
        department_id=payload.department_id, author_id=current_user.id,
    )
    db.add(d)
    current_user.points = (current_user.points or 0) + 4
    db.add(models.PointsLedger(employee_id=current_user.id, points=4, reason="Created discussion"))
    db.commit()
    db.refresh(d)
    return _serialize(db, d, current_user)


@router.post("/{discussion_id}/like")
def like_discussion(discussion_id: int, db: Session = Depends(get_db),
                     current_user: models.Employee = Depends(get_current_user)):
    d = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Discussion not found")
    existing = db.query(models.Like).filter(
        models.Like.discussion_id == discussion_id, models.Like.employee_id == current_user.id
    ).first()
    if existing:
        db.delete(existing)
        d.likes_count = max(0, d.likes_count - 1)
        db.commit()
        return {"liked": False, "likes_count": d.likes_count}

    db.add(models.Like(discussion_id=discussion_id, employee_id=current_user.id))
    d.likes_count += 1
    db.commit()
    return {"liked": True, "likes_count": d.likes_count}


@router.delete("/{discussion_id}")
def delete_discussion(discussion_id: int, db: Session = Depends(get_db),
                       current_user: models.Employee = Depends(get_current_user)):
    d = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Discussion not found")
    if d.author_id != current_user.id and current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(d)
    db.commit()
    return {"message": "Discussion deleted"}
