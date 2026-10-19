from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from .discussions import _serialize as serialize_discussion
from .polls import _serialize_poll

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("", response_model=schemas.SearchResults)
def search(q: str, db: Session = Depends(get_db), current_user: models.Employee = Depends(get_current_user)):
    like = f"%{q}%"
    employees = db.query(models.Employee).filter(models.Employee.name.ilike(like)).limit(10).all()
    posters = db.query(models.Poster).filter(models.Poster.title.ilike(like)).limit(10).all()
    polls = db.query(models.Poll).filter(models.Poll.question.ilike(like)).limit(10).all()
    discussions = db.query(models.Discussion).filter(models.Discussion.title.ilike(like)).limit(10).all()

    return schemas.SearchResults(
        employees=employees,
        posters=posters,
        polls=[_serialize_poll(db, p, current_user) for p in polls],
        discussions=[serialize_discussion(db, d, current_user) for d in discussions],
    )
