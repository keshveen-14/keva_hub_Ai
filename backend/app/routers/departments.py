from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/departments", tags=["Departments"])


@router.get("", response_model=List[schemas.DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).order_by(models.Department.name).all()


@router.post("", response_model=schemas.DepartmentOut)
def create_department(payload: schemas.DepartmentCreate, db: Session = Depends(get_db),
                       admin: models.Employee = Depends(require_admin)):
    if db.query(models.Department).filter(models.Department.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Department already exists")
    dep = models.Department(**payload.model_dump())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db),
                       admin: models.Employee = Depends(require_admin)):
    dep = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(dep)
    db.commit()
    return {"message": "Department deleted"}
