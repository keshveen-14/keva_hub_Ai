from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, ai_service
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])


@router.get("", response_model=List[schemas.QuizOut])
def list_quizzes(department_id: Optional[int] = None, db: Session = Depends(get_db),
                  current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Quiz)
    if department_id:
        query = query.filter(models.Quiz.department_id == department_id)
    return query.order_by(models.Quiz.created_at.desc()).all()


@router.get("/today", response_model=Optional[schemas.QuizOut])
def today_quiz(department_id: Optional[int] = None, db: Session = Depends(get_db),
               current_user: models.Employee = Depends(get_current_user)):
    query = db.query(models.Quiz)
    if department_id:
        query = query.filter(models.Quiz.department_id == department_id)
    return query.order_by(models.Quiz.created_at.desc()).first()


@router.post("/generate", response_model=schemas.QuizOut)
def generate_quiz(payload: schemas.QuizGenerateRequest, db: Session = Depends(get_db),
                   admin: models.Employee = Depends(require_admin)):
    dept = db.query(models.Department).filter(models.Department.id == payload.department_id).first() \
        if payload.department_id else None
    content = ai_service.generate_quiz_content(
        dept.name if dept else "General", payload.topic, payload.num_questions or 5
    )
    quiz = models.Quiz(title=content.get("title", "AI Quiz"), department_id=payload.department_id)
    db.add(quiz)
    db.flush()
    for q in content["questions"]:
        db.add(models.QuizQuestion(
            quiz_id=quiz.id, question=q["question"], option_a=q["option_a"], option_b=q["option_b"],
            option_c=q["option_c"], option_d=q["option_d"], correct_option=q["correct_option"],
        ))
    db.commit()
    db.refresh(quiz)
    return quiz


@router.post("/{quiz_id}/submit")
def submit_quiz(quiz_id: int, payload: schemas.QuizSubmission, db: Session = Depends(get_db),
                 current_user: models.Employee = Depends(get_current_user)):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    score = 0
    total = len(quiz.questions)
    for q in quiz.questions:
        given = payload.answers.get(str(q.id))
        if given and given.upper() == q.correct_option.upper():
            score += 1

    attempt = models.QuizAttempt(quiz_id=quiz_id, employee_id=current_user.id, score=score, total=total)
    db.add(attempt)
    points_earned = score * 3
    current_user.points = (current_user.points or 0) + points_earned
    db.add(models.PointsLedger(employee_id=current_user.id, points=points_earned, reason="Completed quiz"))
    db.commit()
    return {"score": score, "total": total, "points_earned": points_earned}
