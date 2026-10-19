# Installation Guide — KEVA AI Learning Hub

This guide walks through running the project locally from scratch.

## Prerequisites

- Python 3.10+ (`python3 --version`)
- pip
- (Optional) PostgreSQL or MySQL if you don't want to use the default SQLite
- (Optional) An OpenAI or Google Gemini API key for live AI content
  generation — the app works fully without one (offline fallback content)

## Step 1 — Get the files

Unzip the project and open a terminal in the project root
(`keva-ai-learning-hub/`).

## Step 2 — Set up the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and adjust as needed:

```
DATABASE_URL=sqlite:///./keva_ai_hub.db     # default, zero setup
JWT_SECRET_KEY=change-this-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
AI_PROVIDER=openai
OPENAI_API_KEY=                              # optional
GEMINI_API_KEY=                              # optional
```

Leave `OPENAI_API_KEY` / `GEMINI_API_KEY` blank to run entirely offline with
built-in demo content — everything (posters, polls, quizzes, tips, chatbot)
still works.

## Step 4 — Run the server

```bash
uvicorn app.main:app --reload
```

You should see log lines confirming:
- database tables created,
- 10 departments seeded,
- a default admin account seeded (`admin@keva.ai` / `Admin@123`),
- starter posters/polls/quizzes seeded,
- the scheduler started.

## Step 5 — Open the app

- Frontend: **http://localhost:8000/app/index.html**
- API docs (Swagger UI): **http://localhost:8000/docs**
- Health check: **http://localhost:8000/api/health**

Log in with the seeded admin account, or register a new employee account
from the login page.

## Step 6 (optional) — Use PostgreSQL instead of SQLite

1. Install PostgreSQL and create a database:
   ```bash
   createdb keva_ai_hub
   ```
2. In `backend/.env`:
   ```
   DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/keva_ai_hub
   ```
3. Restart the server — tables are created automatically.

## Step 6b (optional) — Use MySQL instead of SQLite

1. Create a database:
   ```sql
   CREATE DATABASE keva_ai_hub CHARACTER SET utf8mb4;
   ```
2. In `backend/.env`:
   ```
   DATABASE_URL=mysql+pymysql://<user>:<password>@localhost:3306/keva_ai_hub
   ```
3. Restart the server.

## Step 7 (optional) — Enable live AI generation

1. Get an API key from OpenAI (`platform.openai.com`) or Google AI Studio
   (Gemini).
2. In `backend/.env`, set `AI_PROVIDER` to `openai` or `gemini` and paste the
   matching key.
3. Restart the server. New posters/polls/quizzes/tips/chatbot replies will
   now be generated live; if a call ever fails, the app automatically falls
   back to offline demo content so nothing breaks.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` on startup | Re-run `pip install -r requirements.txt` inside the activated venv |
| Frontend loads but shows "Session expired" immediately | Clear your browser's localStorage for `localhost:8000` and log in again |
| Port 8000 already in use | Run `uvicorn app.main:app --reload --port 8001` and open that port instead |
| Scheduler jobs never fire | Confirm the server process stays running continuously — jobs are in-process, not external cron |
| Postgres/MySQL connection errors | Confirm the database exists and the user/password/host/port in `DATABASE_URL` are correct |

## Running the frontend separately (advanced)

The frontend is plain static HTML/CSS/JS with no build step, so you can also
serve `frontend/` with any static file server (e.g. `python3 -m http.server`
from inside `frontend/`) as long as the backend's CORS allows it — but the
simplest path is the built-in `/app` mount described above, which requires
no extra configuration.
