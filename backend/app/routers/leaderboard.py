from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=List[schemas.LeaderboardEntry])
def leaderboard(department_id: Optional[int] = None, limit: int = 10, db: Session = Depends(get_db),
                 current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Employee).filter(models.Employee.status == models.StatusEnum.active)
    if department_id:
        query = query.filter(models.Employee.department_id == department_id)
    employees = query.order_by(models.Employee.points.desc()).limit(limit).all()

    return [
        schemas.LeaderboardEntry(
            employee_id=e.id, name=e.name,
            department=e.department.name if e.department else None,
            points=e.points or 0, profile_picture=e.profile_picture, rank=i + 1,
        )
        for i, e in enumerate(employees)
    ]
