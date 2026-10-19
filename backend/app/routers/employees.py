import random
import string
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import hash_password
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _gen_employee_code(db: Session) -> str:
    while True:
        code = "KEVA" + "".join(random.choices(string.digits, k=5))
        if not db.query(models.Employee).filter(models.Employee.employee_code == code).first():
            return code


@router.get("", response_model=List[schemas.EmployeeOut])
def list_employees(
    department_id: Optional[int] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    query = db.query(models.Employee)
    if department_id:
        query = query.filter(models.Employee.department_id == department_id)
    if q:
        query = query.filter(models.Employee.name.ilike(f"%{q}%"))
    return query.order_by(models.Employee.name).all()


@router.get("/{employee_id}", response_model=schemas.EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db),
                  current_user: models.Employee = Depends(get_current_user)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("", response_model=schemas.EmployeeOut)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db),
                     admin: models.Employee = Depends(require_admin)):
    if db.query(models.Employee).filter(models.Employee.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    emp = models.Employee(
        employee_code=_gen_employee_code(db),
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        designation=payload.designation,
        department_id=payload.department_id,
        experience_years=payload.experience_years or 0,
        manager=payload.manager,
        role=models.RoleEnum.admin if payload.role == "admin" else models.RoleEnum.employee,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.put("/{employee_id}", response_model=schemas.EmployeeOut)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db),
                     admin: models.Employee = Depends(require_admin)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(emp, field, value)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db),
                     admin: models.Employee = Depends(require_admin)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted"}
