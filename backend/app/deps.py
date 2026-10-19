"""Reusable FastAPI dependencies: DB session, current user, role guard."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_access_token
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    employee_id = payload.get("sub")
    user = db.query(models.Employee).filter(models.Employee.id == int(employee_id)).first()
    if user is None:
        raise credentials_exception
    if user.status == models.StatusEnum.inactive:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user


def require_admin(current_user: models.Employee = Depends(get_current_user)) -> models.Employee:
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
