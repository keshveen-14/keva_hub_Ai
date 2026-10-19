import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), admin: models.Employee = Depends(require_admin)):
    total_employees = db.query(models.Employee).count()
    active_employees = db.query(models.Employee).filter(
        models.Employee.status == models.StatusEnum.active
    ).count()
    week_ago = dt.datetime.utcnow() - dt.timedelta(days=7)
    active_this_week = db.query(models.Employee).filter(
        models.Employee.last_login_date >= week_ago
    ).count()

    total_posters = db.query(models.Poster).count()
    total_polls = db.query(models.Poll).count()
    total_votes = db.query(models.PollVote).count()
    total_discussions = db.query(models.Discussion).count()
    total_comments = db.query(models.Comment).count()
    total_quiz_attempts = db.query(models.QuizAttempt).count()

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "active_this_week": active_this_week,
        "total_posters": total_posters,
        "total_polls": total_polls,
        "total_votes": total_votes,
        "total_discussions": total_discussions,
        "total_comments": total_comments,
        "total_quiz_attempts": total_quiz_attempts,
    }


@router.get("/department-engagement")
def department_engagement(db: Session = Depends(get_db), admin: models.Employee = Depends(require_admin)):
    departments = db.query(models.Department).all()
    result = []
    for dep in departments:
        employee_count = db.query(models.Employee).filter(models.Employee.department_id == dep.id).count()
        discussion_count = db.query(models.Discussion).filter(models.Discussion.department_id == dep.id).count()
        poll_count = db.query(models.Poll).filter(models.Poll.department_id == dep.id).count()
        votes = db.query(models.PollVote).join(models.Poll).filter(models.Poll.department_id == dep.id).count()
        result.append({
            "department": dep.name,
            "employees": employee_count,
            "discussions": discussion_count,
            "polls": poll_count,
            "votes": votes,
        })
    return result


@router.get("/weekly-activity")
def weekly_activity(db: Session = Depends(get_db), admin: models.Employee = Depends(require_admin)):
    labels, discussions, comments, votes = [], [], [], []
    today = dt.datetime.utcnow().date()
    for i in range(6, -1, -1):
        day = today - dt.timedelta(days=i)
        start = dt.datetime.combine(day, dt.time.min)
        end = dt.datetime.combine(day, dt.time.max)
        labels.append(day.strftime("%a"))
        discussions.append(
            db.query(models.Discussion).filter(
                models.Discussion.created_at >= start, models.Discussion.created_at <= end
            ).count()
        )
        comments.append(
            db.query(models.Comment).filter(
                models.Comment.created_at >= start, models.Comment.created_at <= end
            ).count()
        )
        votes.append(
            db.query(models.PollVote).filter(
                models.PollVote.created_at >= start, models.PollVote.created_at <= end
            ).count()
        )
    return {"labels": labels, "discussions": discussions, "comments": comments, "votes": votes}
