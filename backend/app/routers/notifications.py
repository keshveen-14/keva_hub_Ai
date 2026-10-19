from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=List[schemas.NotificationOut])
def list_notifications(db: Session = Depends(get_db),
                        current_user: models.Employee = Depends(get_current_user)):
    notes = db.query(models.Notification).filter(
        or_(models.Notification.employee_id == current_user.id, models.Notification.employee_id.is_(None))
    ).order_by(models.Notification.created_at.desc()).limit(50).all()
    return notes


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db),
              current_user: models.Employee = Depends(get_current_user)):
    note = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.post("/announce")
def broadcast_announcement(title: str, message: str, db: Session = Depends(get_db),
                            admin: models.Employee = Depends(require_admin)):
    note = models.Notification(employee_id=None, title=title, message=message, type="announcement")
    db.add(note)
    db.commit()
    return {"message": "Announcement sent"}
