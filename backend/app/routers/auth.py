import datetime as dt
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import hash_password, verify_password, create_access_token
from ..deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _gen_employee_code(db: Session) -> str:
    while True:
        code = "KEVA" + "".join(random.choices(string.digits, k=5))
        if not db.query(models.Employee).filter(models.Employee.employee_code == code).first():
            return code


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    if db.query(models.Employee).filter(models.Employee.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = models.Employee(
        employee_code=_gen_employee_code(db),
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        designation=payload.designation,
        department_id=payload.department_id,
        experience_years=payload.experience_years or 0,
        manager=payload.manager,
        role=models.RoleEnum.employee,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    token = create_access_token({"sub": str(employee.id)})
    return schemas.Token(access_token=token, user=employee)


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if not employee or not verify_password(payload.password, employee.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if employee.status == models.StatusEnum.inactive:
        raise HTTPException(status_code=403, detail="Account is inactive. Contact your admin.")

    # streak + points for daily login
    today = dt.datetime.utcnow().date()
    if employee.last_login_date is None or employee.last_login_date.date() != today:
        yesterday = today - dt.timedelta(days=1)
        if employee.last_login_date and employee.last_login_date.date() == yesterday:
            employee.streak_days = (employee.streak_days or 0) + 1
        else:
            employee.streak_days = 1
        employee.last_login_date = dt.datetime.utcnow()
        employee.points = (employee.points or 0) + 5
        db.add(models.PointsLedger(employee_id=employee.id, points=5, reason="Daily login"))
        db.commit()
        db.refresh(employee)

    token = create_access_token({"sub": str(employee.id)})
    return schemas.Token(access_token=token, user=employee)


@router.get("/me", response_model=schemas.EmployeeOut)
def me(current_user: models.Employee = Depends(get_current_user)):
    return current_user
