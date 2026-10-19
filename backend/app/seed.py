"""Seed default departments, an admin account, and starter content."""
import logging
from sqlalchemy.orm import Session

from . import models, ai_service
from .security import hash_password

logger = logging.getLogger("keva.seed")

DEFAULT_DEPARTMENTS = [
    ("AI & Data Science", "fa-brain"),
    ("Software Development", "fa-code"),
    ("HR", "fa-users"),
    ("Marketing", "fa-bullhorn"),
    ("Finance", "fa-coins"),
    ("Sales", "fa-chart-line"),
    ("Cloud", "fa-cloud"),
    ("Cyber Security", "fa-shield-halved"),
    ("DevOps", "fa-infinity"),
    ("Operations", "fa-gears"),
]


def seed(db: Session):
    if db.query(models.Department).count() == 0:
        for name, icon in DEFAULT_DEPARTMENTS:
            db.add(models.Department(name=name, icon=icon, description=f"{name} learning space"))
        db.commit()
        logger.info("Seeded %d departments", len(DEFAULT_DEPARTMENTS))

    if db.query(models.Employee).filter(models.Employee.role == models.RoleEnum.admin).count() == 0:
        ai_dept = db.query(models.Department).filter(models.Department.name == "AI & Data Science").first()
        admin = models.Employee(
            employee_code="KEVA00001",
            name="System Admin",
            email="admin@keva.ai",
            hashed_password=hash_password("Admin@123"),
            designation="Platform Administrator",
            department_id=ai_dept.id if ai_dept else None,
            role=models.RoleEnum.admin,
        )
        db.add(admin)
        db.commit()
        logger.info("Seeded default admin: admin@keva.ai / Admin@123")

    # Starter poster + poll + quiz per department if none exist yet
    if db.query(models.Poster).count() == 0:
        departments = db.query(models.Department).all()
        for dep in departments:
            content = ai_service.generate_poster_content(dep.name)
            db.add(models.Poster(
                title=content.get("title"), explanation=content.get("explanation"),
                key_points=content.get("key_points"), real_world_use_case=content.get("real_world_use_case"),
                best_practices=content.get("best_practices"), example=content.get("example"),
                applications=content.get("applications"), department_id=dep.id,
                image_url="/assets/poster-placeholder.svg",
            ))
        db.commit()
        logger.info("Seeded starter posters")

    if db.query(models.Poll).count() == 0:
        departments = db.query(models.Department).all()
        for dep in departments:
            content = ai_service.generate_poll_content(dep.name)
            poll = models.Poll(question=content["question"], department_id=dep.id)
            db.add(poll)
            db.flush()
            for text in content["options"]:
                db.add(models.PollOption(poll_id=poll.id, text=text))
        db.commit()
        logger.info("Seeded starter polls")

    if db.query(models.Quiz).count() == 0:
        departments = db.query(models.Department).all()
        for dep in departments:
            content = ai_service.generate_quiz_content(dep.name, num_questions=5)
            quiz = models.Quiz(title=content.get("title", "AI Quiz"), department_id=dep.id)
            db.add(quiz)
            db.flush()
            for q in content["questions"]:
                db.add(models.QuizQuestion(
                    quiz_id=quiz.id, question=q["question"], option_a=q["option_a"], option_b=q["option_b"],
                    option_c=q["option_c"], option_d=q["option_d"], correct_option=q["correct_option"],
                ))
        db.commit()
        logger.info("Seeded starter quizzes")
