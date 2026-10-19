from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas, ai_service
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/polls", tags=["Polls"])


def _serialize_poll(db: Session, poll: models.Poll, current_user: models.Employee) -> schemas.PollOut:
    options_out = []
    total_votes = 0
    my_vote = None
    for opt in poll.options:
        count = db.query(models.PollVote).filter(models.PollVote.option_id == opt.id).count()
        total_votes += count
        options_out.append(schemas.PollOptionOut(id=opt.id, text=opt.text, votes=count))
    vote = db.query(models.PollVote).filter(
        models.PollVote.poll_id == poll.id, models.PollVote.employee_id == current_user.id
    ).first()
    if vote:
        my_vote = vote.option_id
    return schemas.PollOut(
        id=poll.id, question=poll.question, department_id=poll.department_id,
        created_at=poll.created_at, options=options_out, total_votes=total_votes,
        my_vote_option_id=my_vote,
    )


@router.get("", response_model=List[schemas.PollOut])
def list_polls(department_id: Optional[int] = None, db: Session = Depends(get_db),
               current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Poll)
    if department_id:
        query = query.filter(models.Poll.department_id == department_id)
    polls = query.order_by(models.Poll.created_at.desc()).all()
    return [_serialize_poll(db, p, current_user) for p in polls]


@router.get("/today", response_model=Optional[schemas.PollOut])
def today_poll(department_id: Optional[int] = None, db: Session = Depends(get_db),
               current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Poll)
    if department_id:
        query = query.filter(models.Poll.department_id == department_id)
    poll = query.order_by(models.Poll.created_at.desc()).first()
    return _serialize_poll(db, poll, current_user) if poll else None


@router.post("", response_model=schemas.PollOut)
def create_poll(payload: schemas.PollCreate, db: Session = Depends(get_db),
                 admin: models.Employee = Depends(require_admin)):
    poll = models.Poll(question=payload.question, department_id=payload.department_id)
    db.add(poll)
    db.flush()
    for text in payload.options:
        db.add(models.PollOption(poll_id=poll.id, text=text))
    db.commit()
    db.refresh(poll)
    _notify_new_poll(db, poll)
    return _serialize_poll(db, poll, admin)


@router.post("/generate", response_model=schemas.PollOut)
def generate_poll(payload: schemas.PollGenerateRequest, db: Session = Depends(get_db),
                   admin: models.Employee = Depends(require_admin)):
    dept = db.query(models.Department).filter(models.Department.id == payload.department_id).first() \
        if payload.department_id else None
    content = ai_service.generate_poll_content(dept.name if dept else "General")
    poll = models.Poll(question=content["question"], department_id=payload.department_id)
    db.add(poll)
    db.flush()
    for text in content["options"]:
        db.add(models.PollOption(poll_id=poll.id, text=text))
    db.commit()
    db.refresh(poll)
    _notify_new_poll(db, poll)
    return _serialize_poll(db, poll, admin)


@router.post("/{poll_id}/vote", response_model=schemas.PollOut)
def vote(poll_id: int, payload: schemas.VoteRequest, db: Session = Depends(get_db),
         current_user: models.Employee = Depends(get_current_user)):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    existing = db.query(models.PollVote).filter(
        models.PollVote.poll_id == poll_id, models.PollVote.employee_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already voted on this poll")
    option = db.query(models.PollOption).filter(
        models.PollOption.id == payload.option_id, models.PollOption.poll_id == poll_id
    ).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    db.add(models.PollVote(poll_id=poll_id, option_id=payload.option_id, employee_id=current_user.id))
    current_user.points = (current_user.points or 0) + 2
    db.add(models.PointsLedger(employee_id=current_user.id, points=2, reason="Voted on poll"))
    db.commit()
    db.refresh(poll)
    return _serialize_poll(db, poll, current_user)


def _notify_new_poll(db: Session, poll: models.Poll):
    db.add(models.Notification(
        employee_id=None,
        title="New Poll Started",
        message=poll.question,
        type="poll",
    ))
    db.commit()
