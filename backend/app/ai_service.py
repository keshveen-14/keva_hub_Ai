"""
AI content generation service.

Uses OpenAI (or Google Gemini) to generate posters, polls, quizzes,
tips and discussion prompts. If no API key is configured, falls back
to a curated local content bank so the app is fully usable out of the box.

Configure via .env:
  AI_PROVIDER=openai        # or "gemini"
  OPENAI_API_KEY=sk-...
  GEMINI_API_KEY=...
"""
import os
import json
import random

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

TOPIC_BANK = {
    "AI & Data Science": ["Neural Networks", "Prompt Engineering", "Vector Databases", "Model Fine-Tuning", "Data Pipelines"],
    "Software Development": ["AI Pair Programming", "Code Review with AI", "AI-Assisted Testing", "Refactoring with LLMs"],
    "HR": ["AI in Recruitment", "AI for Employee Wellbeing", "Bias in AI Hiring Tools", "AI Onboarding Assistants"],
    "Marketing": ["AI Content Generation", "Personalization Engines", "AI-Driven Ad Targeting", "Generative Design"],
    "Finance": ["AI Fraud Detection", "Algorithmic Trading Basics", "AI in Risk Modeling", "Automated Reporting"],
    "Sales": ["AI Sales Assistants", "Predictive Lead Scoring", "Conversational AI in CRM"],
    "Cloud": ["AI Workload Scaling", "MLOps on the Cloud", "Serverless AI Inference"],
    "Cyber Security": ["AI Threat Detection", "Adversarial AI", "AI in SOC Automation"],
    "DevOps": ["AI in CI/CD", "Anomaly Detection in Ops", "AIOps Fundamentals"],
    "Operations": ["AI for Process Automation", "Demand Forecasting with AI", "AI Supply Chain Optimization"],
    "General": ["What is a Large Language Model?", "AI Ethics 101", "Understanding Tokens", "AI vs Machine Learning vs Deep Learning"],
}


def _client_available() -> bool:
    return bool(OPENAI_API_KEY) or bool(GEMINI_API_KEY)


def _pick_topic(department_name: str) -> str:
    bank = TOPIC_BANK.get(department_name, TOPIC_BANK["General"])
    return random.choice(bank)


def _call_openai(prompt: str) -> str:
    import requests
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(prompt: str) -> str:
    import requests
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _generate_json(prompt: str) -> dict:
    """Call the configured provider and parse a JSON object from the response."""
    text = _call_gemini(prompt) if AI_PROVIDER == "gemini" and GEMINI_API_KEY else _call_openai(prompt)
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text)


# ------------------------------------------------------------------ Posters
def generate_poster_content(department_name: str = "General", topic: str = None) -> dict:
    topic = topic or _pick_topic(department_name)

    if _client_available():
        prompt = (
            f"Create an employee learning poster about '{topic}' for the "
            f"'{department_name}' department. Return STRICT JSON only with keys: "
            "title, explanation (2-3 sentences), key_points (5 bullet lines separated by \\n), "
            "real_world_use_case, best_practices, example, applications. No markdown."
        )
        try:
            data = _generate_json(prompt)
            data.setdefault("title", topic)
            return data
        except Exception:
            pass  # fall through to local content bank

    return {
        "title": f"Understanding {topic}",
        "explanation": (
            f"{topic} is a foundational AI concept relevant to {department_name}. "
            "This poster breaks it down into simple, practical terms so you can "
            "apply it in your daily work."
        ),
        "key_points": (
            f"• What {topic} means in practice\n"
            "• Why it matters for your role\n"
            "• Common tools that use this concept\n"
            "• A quick mental model to remember it\n"
            "• One thing to try this week"
        ),
        "real_world_use_case": f"Teams use {topic} to speed up decisions and reduce manual, repetitive work.",
        "best_practices": "Start small, validate outputs with a human, and document what works.",
        "example": f"Example: applying {topic} to a real task in {department_name} to save time on a recurring process.",
        "applications": f"{department_name} workflows, reporting, and day-to-day decision support.",
    }


# --------------------------------------------------------------------- Polls
def generate_poll_content(department_name: str = "General") -> dict:
    if _client_available():
        prompt = (
            f"Create one short AI-related poll question for the '{department_name}' "
            "department with 4 short answer options. Return STRICT JSON only: "
            '{"question": "...", "options": ["...","...","...","..."]}'
        )
        try:
            data = _generate_json(prompt)
            if data.get("question") and len(data.get("options", [])) >= 2:
                return data
        except Exception:
            pass

    fallback_polls = [
        {"question": "Which AI model do you use most often?", "options": ["GPT", "Claude", "Gemini", "DeepSeek"]},
        {"question": "How comfortable are you using AI tools at work?", "options": ["Very comfortable", "Somewhat", "Just starting", "Not yet"]},
        {"question": f"What's the most useful AI application for {department_name}?", "options": ["Automation", "Content generation", "Data analysis", "Chatbots"]},
        {"question": "How often do you use AI tools in your daily work?", "options": ["Daily", "Weekly", "Occasionally", "Rarely"]},
    ]
    return random.choice(fallback_polls)


# -------------------------------------------------------------------- Quiz
def generate_quiz_content(department_name: str = "General", topic: str = None, num_questions: int = 5) -> dict:
    topic = topic or _pick_topic(department_name)

    if _client_available():
        prompt = (
            f"Create a {num_questions}-question multiple choice quiz about '{topic}' "
            f"for the '{department_name}' department. Return STRICT JSON only: "
            '{"title": "...", "questions": [{"question":"...","option_a":"...","option_b":"...",'
            '"option_c":"...","option_d":"...","correct_option":"A"}]}'
        )
        try:
            data = _generate_json(prompt)
            if data.get("questions"):
                return data
        except Exception:
            pass

    bank = [
        {
            "question": f"What best describes {topic}?",
            "option_a": "A core AI/technology concept applied at work",
            "option_b": "A type of spreadsheet formula",
            "option_c": "A hardware component",
            "option_d": "A company holiday",
            "correct_option": "A",
        },
        {
            "question": "AI tools are most helpful when they:",
            "option_a": "Replace all human review",
            "option_b": "Assist and speed up human decision-making",
            "option_c": "Are never checked for accuracy",
            "option_d": "Are used without any data privacy care",
            "correct_option": "B",
        },
        {
            "question": "A good practice when using AI-generated content is to:",
            "option_a": "Publish it immediately without review",
            "option_b": "Ignore company data policies",
            "option_c": "Review and validate before using it",
            "option_d": "Never document what worked",
            "correct_option": "C",
        },
        {
            "question": "Which of these is a common AI application area?",
            "option_a": "Predictive analytics",
            "option_b": "Manual paper filing",
            "option_c": "Postal mail sorting by hand",
            "option_d": "None of the above",
            "correct_option": "A",
        },
        {
            "question": f"In {department_name}, AI can primarily help by:",
            "option_a": "Increasing manual repetitive work",
            "option_b": "Automating repetitive tasks and surfacing insights",
            "option_c": "Removing the need for any expertise",
            "option_d": "Slowing down reporting",
            "correct_option": "B",
        },
    ]
    random.shuffle(bank)
    return {"title": f"Quiz: {topic}", "questions": bank[:num_questions]}


# ---------------------------------------------------------------- Tip / Q's
def generate_ai_tip(department_name: str = "General") -> str:
    topic = _pick_topic(department_name)
    tips = [
        f"Try asking an AI assistant to summarize your longest doc today — it's a fast way to explore {topic}.",
        f"Pair AI output with a quick human review — it's the best practice for {topic}.",
        f"Spend 5 minutes today exploring how {topic} could simplify one repetitive task.",
    ]
    return random.choice(tips)


def generate_discussion_question(department_name: str = "General") -> str:
    topic = _pick_topic(department_name)
    return f"How could {topic} change the way {department_name} works over the next year? Share your thoughts!"


def chatbot_reply(message: str, history: list = None) -> str:
    """Simple AI chatbot reply, using the configured provider with a graceful fallback."""
    if _client_available():
        try:
            context = "\n".join(f"{h['role']}: {h['content']}" for h in (history or [])[-6:])
            prompt = (
                "You are KEVA, a friendly internal AI learning assistant for company employees. "
                "Answer clearly and concisely, focused on helping employees learn AI concepts.\n"
                f"{context}\nuser: {message}\nassistant:"
            )
            text = _call_gemini(prompt) if AI_PROVIDER == "gemini" and GEMINI_API_KEY else _call_openai(prompt)
            return text.strip()
        except Exception:
            pass

    return (
        "I'm KEVA, your AI learning assistant! (Running in offline demo mode right now — "
        "add an OPENAI_API_KEY or GEMINI_API_KEY in backend/.env to enable live AI answers.) "
        f"About '{message[:60]}...' — try checking today's poster or poll for related insights, "
        "or ask your department's discussion board."
    )
