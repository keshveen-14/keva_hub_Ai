"""Pydantic schemas (request/response models)."""
import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# --------------------------------------------------------------- Department
class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = "fa-diagram-project"


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ----------------------------------------------------------------- Employee
class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    designation: Optional[str] = "Employee"
    department_id: Optional[int] = None
    experience_years: Optional[int] = 0
    manager: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    password: str
    role: Optional[str] = "employee"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    department_id: Optional[int] = None
    experience_years: Optional[int] = None
    manager: Optional[str] = None
    status: Optional[str] = None
    profile_picture: Optional[str] = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: Optional[str]
    name: str
    email: EmailStr
    designation: Optional[str]
    department_id: Optional[int]
    profile_picture: Optional[str]
    experience_years: Optional[int]
    join_date: Optional[dt.datetime]
    manager: Optional[str]
    status: Optional[str]
    role: Optional[str]
    points: Optional[int]
    streak_days: Optional[int]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: EmployeeOut


# ------------------------------------------------------------------- Poster
class PosterBase(BaseModel):
    title: str
    explanation: Optional[str] = None
    key_points: Optional[str] = None
    real_world_use_case: Optional[str] = None
    best_practices: Optional[str] = None
    example: Optional[str] = None
    applications: Optional[str] = None
    department_id: Optional[int] = None
    image_url: Optional[str] = None


class PosterCreate(PosterBase):
    pass


class PosterGenerateRequest(BaseModel):
    department_id: Optional[int] = None
    topic: Optional[str] = None


class PosterOut(PosterBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: dt.datetime
    image_url: str


# --------------------------------------------------------------------- Poll
class PollOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    votes: int = 0


class PollCreate(BaseModel):
    question: str
    options: List[str]
    department_id: Optional[int] = None


class PollGenerateRequest(BaseModel):
    department_id: Optional[int] = None


class PollOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question: str
    department_id: Optional[int]
    created_at: dt.datetime
    options: List[PollOptionOut]
    total_votes: int = 0
    my_vote_option_id: Optional[int] = None


class VoteRequest(BaseModel):
    option_id: int


# --------------------------------------------------------------- Discussion
class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    author_id: int
    author_name: Optional[str] = None
    created_at: dt.datetime


class DiscussionCreate(BaseModel):
    title: str
    content: str
    department_id: Optional[int] = None
    image_url: Optional[str] = None


class DiscussionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    image_url: Optional[str]
    author_id: int
    author_name: Optional[str] = None
    department_id: Optional[int]
    likes_count: int
    comments_count: int = 0
    liked_by_me: bool = False
    created_at: dt.datetime


# -------------------------------------------------------------------- Quiz
class QuizQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    department_id: Optional[int]
    questions: List[QuizQuestionOut]


class QuizSubmission(BaseModel):
    answers: dict  # {question_id: "A"}


class QuizGenerateRequest(BaseModel):
    department_id: Optional[int] = None
    topic: Optional[str] = None
    num_questions: Optional[int] = 5


# ------------------------------------------------------------- Notification
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: dt.datetime


# ------------------------------------------------------------------- Leaderboard
class LeaderboardEntry(BaseModel):
    employee_id: int
    name: str
    department: Optional[str]
    points: int
    profile_picture: Optional[str]
    rank: int


# --------------------------------------------------------------------- Misc
class SearchResults(BaseModel):
    employees: List[EmployeeOut] = []
    posters: List[PosterOut] = []
    polls: List[PollOut] = []
    discussions: List[DiscussionOut] = []
