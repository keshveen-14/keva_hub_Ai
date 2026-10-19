from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, ai_service
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/posters", tags=["Posters"])

PLACEHOLDER_IMAGES = [
    "/assets/poster-placeholder.svg",
]


@router.get("", response_model=List[schemas.PosterOut])
def list_posters(department_id: Optional[int] = None, db: Session = Depends(get_db),
                  current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Poster)
    if department_id:
        query = query.filter(models.Poster.department_id == department_id)
    return query.order_by(models.Poster.created_at.desc()).all()


@router.get("/today", response_model=Optional[schemas.PosterOut])
def today_poster(department_id: Optional[int] = None, db: Session = Depends(get_db),
                  current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Poster)
    if department_id:
        query = query.filter(models.Poster.department_id == department_id)
    return query.order_by(models.Poster.created_at.desc()).first()


@router.get("/{poster_id}", response_model=schemas.PosterOut)
def get_poster(poster_id: int, db: Session = Depends(get_db),
               current_user: models.Employee = Depends(get_current_user)):
    poster = db.query(models.Poster).filter(models.Poster.id == poster_id).first()
    if not poster:
        raise HTTPException(status_code=404, detail="Poster not found")
    # award small points for reading
    current_user.points = (current_user.points or 0) + 1
    db.add(models.PointsLedger(employee_id=current_user.id, points=1, reason="Read poster"))
    db.commit()
    return poster


@router.post("", response_model=schemas.PosterOut)
def create_poster(payload: schemas.PosterCreate, db: Session = Depends(get_db),
                   admin: models.Employee = Depends(require_admin)):
    poster = models.Poster(**payload.model_dump(), image_url=payload.image_url or PLACEHOLDER_IMAGES[0])
    db.add(poster)
    db.commit()
    db.refresh(poster)
    _notify_new_poster(db, poster)
    return poster


@router.post("/generate", response_model=schemas.PosterOut)
def generate_poster(payload: schemas.PosterGenerateRequest, db: Session = Depends(get_db),
                     admin: models.Employee = Depends(require_admin)):
    dept = db.query(models.Department).filter(models.Department.id == payload.department_id).first() \
        if payload.department_id else None
    content = ai_service.generate_poster_content(dept.name if dept else "General", payload.topic)
    poster = models.Poster(
        title=content.get("title", "AI Learning Poster"),
        explanation=content.get("explanation"),
        key_points=content.get("key_points"),
        real_world_use_case=content.get("real_world_use_case"),
        best_practices=content.get("best_practices"),
        example=content.get("example"),
        applications=content.get("applications"),
        department_id=payload.department_id,
        image_url=PLACEHOLDER_IMAGES[0],
    )
    db.add(poster)
    db.commit()
    db.refresh(poster)
    _notify_new_poster(db, poster)
    return poster


@router.post("/{poster_id}/bookmark")
def bookmark_poster(poster_id: int, db: Session = Depends(get_db),
                     current_user: models.Employee = Depends(get_current_user)):
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.poster_id == poster_id, models.Bookmark.employee_id == current_user.id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"bookmarked": False}
    db.add(models.Bookmark(poster_id=poster_id, employee_id=current_user.id))
    db.commit()
    return {"bookmarked": True}


@router.get("/bookmarks/mine", response_model=List[schemas.PosterOut])
def my_bookmarks(db: Session = Depends(get_db), current_user: models.Employee = Depends(get_current_user)):
    marks = db.query(models.Bookmark).filter(models.Bookmark.employee_id == current_user.id).all()
    return [m.poster for m in marks]


def _notify_new_poster(db: Session, poster: models.Poster):
    db.add(models.Notification(
        employee_id=None,
        title="New AI Poster Available",
        message=f"Today's poster: {poster.title}",
        type="poster",
    ))
    db.commit()
