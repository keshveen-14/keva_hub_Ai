"""SQLAlchemy ORM models for KEVA AI Learning Hub."""
import enum
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum,
    UniqueConstraint, Table
)
from sqlalchemy.orm import relationship
from .database import Base


def now():
    return dt.datetime.utcnow()


class RoleEnum(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class StatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


# ---------------------------------------------------------------- Department
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    icon = Column(String(50), default="fa-diagram-project")  # font-awesome class
    created_at = Column(DateTime, default=now)

    employees = relationship("Employee", back_populates="department")
    posters = relationship("Poster", back_populates="department")
    polls = relationship("Poll", back_populates="department")
    discussions = relationship("Discussion", back_populates="department")


# ------------------------------------------------------------------ Employee
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    designation = Column(String(100), default="Employee")
    profile_picture = Column(String(255), default="/assets/default-avatar.png")
    experience_years = Column(Integer, default=0)
    join_date = Column(DateTime, default=now)
    manager = Column(String(120), nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.active)
    role = Column(Enum(RoleEnum), default=RoleEnum.employee)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="employees")

    points = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_login_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=now)

    discussions = relationship("Discussion", back_populates="author")
    comments = relationship("Comment", back_populates="author")


# -------------------------------------------------------------------- Poster
class Poster(Base):
    __tablename__ = "posters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    explanation = Column(Text)
    key_points = Column(Text)          # newline separated
    real_world_use_case = Column(Text)
    best_practices = Column(Text)
    example = Column(Text)
    applications = Column(Text)
    image_url = Column(String(255), default="/assets/poster-placeholder.svg")

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="posters")

    created_at = Column(DateTime, default=now)
    bookmarks = relationship("Bookmark", back_populates="poster")


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    poster_id = Column(Integer, ForeignKey("posters.id"))
    created_at = Column(DateTime, default=now)
    poster = relationship("Poster", back_populates="bookmarks")
    __table_args__ = (UniqueConstraint("employee_id", "poster_id", name="uq_bookmark"),)


# ---------------------------------------------------------------------- Poll
class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(300), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="polls")
    created_at = Column(DateTime, default=now)

    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")


class PollOption(Base):
    __tablename__ = "poll_options"
    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    text = Column(String(150), nullable=False)
    poll = relationship("Poll", back_populates="options")


class PollVote(Base):
    __tablename__ = "poll_votes"
    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    option_id = Column(Integer, ForeignKey("poll_options.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    created_at = Column(DateTime, default=now)
    poll = relationship("Poll", back_populates="votes")
    __table_args__ = (UniqueConstraint("poll_id", "employee_id", name="uq_one_vote_per_poll"),)


# --------------------------------------------------------------- Discussion
class Discussion(Base):
    __tablename__ = "discussions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    image_url = Column(String(255), nullable=True)

    author_id = Column(Integer, ForeignKey("employees.id"))
    author = relationship("Employee", back_populates="discussions")

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="discussions")

    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)

    comments = relationship("Comment", back_populates="discussion", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="discussion", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    author_id = Column(Integer, ForeignKey("employees.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)

    discussion = relationship("Discussion", back_populates="comments")
    author = relationship("Employee", back_populates="comments")


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    discussion = relationship("Discussion", back_populates="likes")
    __table_args__ = (UniqueConstraint("discussion_id", "employee_id", name="uq_one_like"),)


# ------------------------------------------------------------------- Quiz
class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=now)
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question = Column(Text)
    option_a = Column(String(200))
    option_b = Column(String(200))
    option_c = Column(String(200))
    option_d = Column(String(200))
    correct_option = Column(String(1))  # A/B/C/D
    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)


# ------------------------------------------------------------- Notification
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # null = broadcast
    title = Column(String(200))
    message = Column(String(500))
    type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


# ---------------------------------------------------------- Points / Ledger
class PointsLedger(Base):
    __tablename__ = "points_ledger"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    points = Column(Integer)
    reason = Column(String(150))
    created_at = Column(DateTime, default=now)
