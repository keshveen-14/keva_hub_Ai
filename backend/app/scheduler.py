"""
APScheduler jobs.

- 4:00 PM daily -> generate an AI poster for every department
- 5:00 PM daily -> generate an AI poll for every department
- 9:00 AM daily -> generate an AI quiz for every department (bonus)
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import SessionLocal
from . import models, ai_service

logger = logging.getLogger("keva.scheduler")


def generate_posters_job():
    db = SessionLocal()
    try:
        departments = db.query(models.Department).all()
        for dep in departments:
            content = ai_service.generate_poster_content(dep.name)
            poster = models.Poster(
                title=content.get("title", "AI Learning Poster"),
                explanation=content.get("explanation"),
                key_points=content.get("key_points"),
                real_world_use_case=content.get("real_world_use_case"),
                best_practices=content.get("best_practices"),
                example=content.get("example"),
                applications=content.get("applications"),
                department_id=dep.id,
                image_url="/assets/poster-placeholder.svg",
            )
            db.add(poster)
            db.flush()
            db.add(models.Notification(
                employee_id=None, title="New AI Poster Available",
                message=f"Today's poster for {dep.name}: {poster.title}", type="poster",
            ))
        db.commit()
        logger.info("Generated daily posters for %d departments", len(departments))
    except Exception:
        logger.exception("Failed to generate daily posters")
        db.rollback()
    finally:
        db.close()


def generate_polls_job():
    db = SessionLocal()
    try:
        departments = db.query(models.Department).all()
        for dep in departments:
            content = ai_service.generate_poll_content(dep.name)
            poll = models.Poll(question=content["question"], department_id=dep.id)
            db.add(poll)
            db.flush()
            for text in content["options"]:
                db.add(models.PollOption(poll_id=poll.id, text=text))
            db.add(models.Notification(
                employee_id=None, title="New Poll Started",
                message=f"{dep.name}: {poll.question}", type="poll",
            ))
        db.commit()
        logger.info("Generated daily polls for %d departments", len(departments))
    except Exception:
        logger.exception("Failed to generate daily polls")
        db.rollback()
    finally:
        db.close()


def generate_quizzes_job():
    db = SessionLocal()
    try:
        departments = db.query(models.Department).all()
        for dep in departments:
            content = ai_service.generate_quiz_content(dep.name, num_questions=5)
            quiz = models.Quiz(title=content.get("title", "AI Quiz"), department_id=dep.id)
            db.add(quiz)
            db.flush()
            for q in content["questions"]:
                db.add(models.QuizQuestion(
                    quiz_id=quiz.id, question=q["question"], option_a=q["option_a"],
                    option_b=q["option_b"], option_c=q["option_c"], option_d=q["option_d"],
                    correct_option=q["correct_option"],
                ))
        db.commit()
        logger.info("Generated daily quizzes for %d departments", len(departments))
    except Exception:
        logger.exception("Failed to generate daily quizzes")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(generate_posters_job, CronTrigger(hour=16, minute=0), id="daily_poster", replace_existing=True)
    scheduler.add_job(generate_polls_job, CronTrigger(hour=17, minute=0), id="daily_poll", replace_existing=True)
    scheduler.add_job(generate_quizzes_job, CronTrigger(hour=9, minute=0), id="daily_quiz", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started: posters @16:00, polls @17:00, quizzes @09:00 (Asia/Kolkata)")
    return scheduler
