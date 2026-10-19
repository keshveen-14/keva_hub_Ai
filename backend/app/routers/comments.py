from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/discussions", tags=["Comments"])


@router.get("/{discussion_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(discussion_id: int, db: Session = Depends(get_db),
                   current_user: models.Employee = Depends(get_current_user)):
    comments = db.query(models.Comment).filter(
        models.Comment.discussion_id == discussion_id
    ).order_by(models.Comment.created_at).all()
    return [
        schemas.CommentOut(
            id=c.id, content=c.content, author_id=c.author_id,
            author_name=c.author.name if c.author else None, created_at=c.created_at,
        ) for c in comments
    ]


@router.post("/{discussion_id}/comments", response_model=schemas.CommentOut)
def add_comment(discussion_id: int, payload: schemas.CommentCreate, db: Session = Depends(get_db),
                 current_user: models.Employee = Depends(get_current_user)):
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    comment = models.Comment(discussion_id=discussion_id, author_id=current_user.id, content=payload.content)
    db.add(comment)
    current_user.points = (current_user.points or 0) + 2
    db.add(models.PointsLedger(employee_id=current_user.id, points=2, reason="Commented"))

    if discussion.author_id != current_user.id:
        db.add(models.Notification(
            employee_id=discussion.author_id,
            title="New reply to your discussion",
            message=f"{current_user.name} replied to '{discussion.title}'",
            type="reply",
        ))
    db.commit()
    db.refresh(comment)
    return schemas.CommentOut(
        id=comment.id, content=comment.content, author_id=comment.author_id,
        author_name=current_user.name, created_at=comment.created_at,
    )


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db),
                    current_user: models.Employee = Depends(get_current_user)):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id and current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}
