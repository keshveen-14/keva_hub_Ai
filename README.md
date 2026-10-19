# KEVA AI Learning Hub

An internal company web portal where employees learn AI through daily
AI-generated posters, polls, quizzes, community discussions, an AI chatbot,
and a points-based leaderboard — filtered per department.

Built as a working full-stack project:

- **Backend:** FastAPI, SQLAlchemy, JWT auth, APScheduler, OpenAI/Gemini
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5, Font Awesome, Chart.js
- **Database:** SQLite by default (zero setup), PostgreSQL/MySQL supported

---

## 1. What's included

```
keva-ai-learning-hub/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, mounts frontend + API routers
│   │   ├── database.py        SQLAlchemy engine/session (SQLite/Postgres/MySQL)
│   │   ├── models.py          ORM models (Employee, Department, Poster, Poll…)
│   │   ├── schemas.py         Pydantic request/response schemas
│   │   ├── security.py        Password hashing + JWT
│   │   ├── deps.py            Auth dependencies (current user / admin guard)
│   │   ├── ai_service.py      OpenAI/Gemini content generation (+ offline fallback)
│   │   ├── scheduler.py       APScheduler jobs (4pm poster, 5pm poll, 9am quiz)
│   │   ├── seed.py            Seeds departments, admin account, starter content
│   │   └── routers/           auth, employees, departments, posters, polls,
│   │                          discussions, comments, quizzes, notifications,
│   │                          leaderboard, analytics, search, chatbot, daily
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html             Login / Register
│   ├── dashboard.html         Poster, poll, discussions, leaderboard, tip, activity
│   ├── discussions.html       Community board (create/reply/like/sort)
│   ├── quiz.html              Daily AI quiz
│   ├── leaderboard.html       Podium + full rankings
│   ├── profile.html           Employee profile, bookmarks, badges
│   ├── admin.html             Employee/department management, AI content generation
│   ├── analytics.html         Charts: weekly activity, department engagement
│   ├── css/style.css          Design system (corporate light/dark theme)
│   ├── js/                    api.js, app.js (shared shell), and one file per page
│   └── assets/                Poster placeholder graphic, default avatar
└── README.md / INSTALLATION.md
```

## 2. Quick start

```bash
cd backend
python3 -m venv venv && source venv/bin/activate      # optional but recommended
pip install -r requirements.txt
cp .env.example .env                                   # edit if needed
uvicorn app.main:app --reload
```

Then open **http://localhost:8000/app/index.html** in your browser.

The FastAPI app serves both the API (`/api/...`) and the static frontend
(`/app/...`) from the same process — no separate frontend server needed.
Interactive API docs are at **http://localhost:8000/docs**.

On first run the app automatically:
- creates all database tables,
- seeds the 10 default departments,
- creates a default admin account: **admin@keva.ai / Admin@123**,
- generates a starter poster, poll and quiz per department.

See `INSTALLATION.md` for a fully detailed, step-by-step setup guide
(including PostgreSQL/MySQL configuration).

## 3. AI content generation

`backend/app/ai_service.py` calls OpenAI (`gpt-4o-mini`) or Google Gemini
(`gemini-1.5-flash`) to generate posters, polls, quizzes, tips, and discussion
prompts. Set these in `backend/.env`:

```
AI_PROVIDER=openai        # or "gemini"
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

**No key configured?** The app still works fully — `ai_service.py` falls
back to a curated, department-aware content bank so posters/polls/quizzes/tips
generate instantly offline. This is the default out of the box, ideal for
demos and evaluation before you wire up a paid API key.

## 4. Scheduled content

`backend/app/scheduler.py` runs three daily jobs via APScheduler (timezone
`Asia/Kolkata`, edit the `CronTrigger` calls to change):

| Time  | Job                          |
|-------|-------------------------------|
| 4:00 PM | Generate a new AI poster per department |
| 5:00 PM | Generate a new AI poll per department   |
| 9:00 AM | Generate a new AI quiz per department   |

Admins can also trigger any of these on demand from **Admin → Generate AI
Content**.

## 5. Roles & permissions

- **Employee:** register/login, view department-filtered content, vote on
  polls, create/reply/like discussions, take quizzes, bookmark posters, view
  leaderboard, chat with the AI assistant.
- **Admin:** everything above, plus add/deactivate/delete employees, manage
  departments, manually generate AI content, broadcast announcements, and
  view the analytics dashboard.

Role is enforced server-side (`require_admin` dependency) on every
admin-only endpoint, not just hidden in the UI.

## 6. Security

- JWT bearer authentication (`python-jose`), tokens expire after 24h by default
- Passwords hashed with bcrypt (`passlib`)
- Role-based access control (admin vs employee) enforced on the API
- Pydantic request validation on every endpoint
- SQLAlchemy ORM (parameterized queries) — no raw SQL string building
- CORS configured (tighten `allow_origins` for production)

## 7. Switching to PostgreSQL or MySQL

Edit `backend/.env`:

```
# PostgreSQL
DATABASE_URL=postgresql+psycopg2://keva_user:keva_pass@localhost:5432/keva_ai_hub

# MySQL
DATABASE_URL=mysql+pymysql://keva_user:keva_pass@localhost:3306/keva_ai_hub
```

Create the database first (`createdb keva_ai_hub` / `CREATE DATABASE keva_ai_hub;`),
then just start the app — tables are created automatically on startup.

## 8. Notes & next steps for production

- Set a strong, unique `JWT_SECRET_KEY` in `.env`.
- Put this behind HTTPS (nginx/Caddy) and restrict CORS `allow_origins`.
- Swap SQLite for Postgres/MySQL for multi-user concurrent access.
- Move file/image uploads (profile pictures, discussion images) to real
  object storage (S3, GCS, Azure Blob) — the schema already stores plain
  URLs, so this is a drop-in change.
- Add a process manager (systemd/pm2/Docker) so the scheduler survives
  restarts and only one instance runs the daily jobs.
