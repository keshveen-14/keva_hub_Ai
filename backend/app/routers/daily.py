import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, ai_service
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/daily", tags=["Daily AI Content"])

_tip_cache = {}
_question_cache = {}


@router.get("/tip")
def ai_tip_of_the_day(department_id: Optional[int] = None, db: Session = Depends(get_db),
                       current_user: models.Employee = Depends(get_current_user)):
    dept = db.query(models.Department).filter(models.Department.id == department_id).first() \
        if department_id else None
    key = (dept.name if dept else "General", dt.date.today())
    if key not in _tip_cache:
        _tip_cache[key] = ai_service.generate_ai_tip(dept.name if dept else "General")
    return {"tip": _tip_cache[key]}


@router.get("/discussion-question")
def ai_discussion_question(department_id: Optional[int] = None, db: Session = Depends(get_db),
                            current_user: models.Employee = Depends(get_current_user)):
    dept = db.query(models.Department).filter(models.Department.id == department_id).first() \
        if department_id else None
    key = (dept.name if dept else "General", dt.date.today())
    if key not in _question_cache:
        _question_cache[key] = ai_service.generate_discussion_question(dept.name if dept else "General")
    return {"question": _question_cache[key]}
