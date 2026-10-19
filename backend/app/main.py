import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine, SessionLocal
from . import models, seed
from .scheduler import start_scheduler
from .routers import (
    auth, employees, departments, posters, polls, discussions,
    comments, quizzes, notifications, leaderboard, analytics, search,
    chatbot, daily,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("keva")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KEVA AI Learning Hub",
    description="Internal employee AI learning portal — posters, polls, discussions, quizzes, leaderboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- routers ---
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(departments.router)
app.include_router(posters.router)
app.include_router(polls.router)
app.include_router(discussions.router)
app.include_router(comments.router)
app.include_router(quizzes.router)
app.include_router(notifications.router)
app.include_router(leaderboard.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(chatbot.router)
app.include_router(daily.router)

# --- serve the frontend (static site) ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "KEVA AI Learning Hub API"}


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        seed.seed(db)
    finally:
        db.close()
    app.state.scheduler = start_scheduler()
    logger.info("KEVA AI Learning Hub API started. Docs at /docs — Frontend at /app")
