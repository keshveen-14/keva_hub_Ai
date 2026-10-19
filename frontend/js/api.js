/* Central API client for KEVA AI Learning Hub.
   The frontend is served by the same FastAPI app (at /app), so the API
   is always reachable at a same-origin relative "/api" path. */
const KEVA_API_BASE = "/api";

const KevaAPI = {
  token() { return localStorage.getItem("keva_token"); },

  setToken(t) { localStorage.setItem("keva_token", t); },

  clearSession() {
    localStorage.removeItem("keva_token");
    localStorage.removeItem("keva_user");
  },

  currentUser() {
    const raw = localStorage.getItem("keva_user");
    return raw ? JSON.parse(raw) : null;
  },

  setCurrentUser(u) { localStorage.setItem("keva_user", JSON.stringify(u)); },

  async request(path, { method = "GET", body = null, auth = true, params = null } = {}) {
    let url = `${KEVA_API_BASE}${path}`;
    if (params) {
      const qs = Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null && v !== "")
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join("&");
      if (qs) url += (url.includes("?") ? "&" : "?") + qs;
    }
    const headers = { "Content-Type": "application/json" };
    if (auth && this.token()) headers["Authorization"] = `Bearer ${this.token()}`;

    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
      this.clearSession();
      if (!window.location.pathname.endsWith("index.html") && window.location.pathname !== "/") {
        window.location.href = "index.html";
      }
      throw new Error("Session expired. Please log in again.");
    }

    let data = null;
    try { data = await res.json(); } catch (e) { /* no body */ }

    if (!res.ok) {
      const message = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return data;
  },

  get(path, params) { return this.request(path, { method: "GET", params }); },
  post(path, body) { return this.request(path, { method: "POST", body }); },
  put(path, body) { return this.request(path, { method: "PUT", body }); },
  del(path) { return this.request(path, { method: "DELETE" }); },

  // ---- Auth
  login(email, password) { return this.request("/auth/login", { method: "POST", body: { email, password }, auth: false }); },
  register(payload) { return this.request("/auth/register", { method: "POST", body: payload, auth: false }); },
  me() { return this.get("/auth/me"); },

  // ---- Departments
  departments() { return this.get("/departments"); },

  // ---- Posters
  todayPoster(department_id) { return this.get("/posters/today", { department_id }); },
  posters(department_id) { return this.get("/posters", { department_id }); },
  generatePoster(payload) { return this.post("/posters/generate", payload); },
  bookmarkPoster(id) { return this.post(`/posters/${id}/bookmark`); },
  myBookmarks() { return this.get("/posters/bookmarks/mine"); },

  // ---- Polls
  todayPoll(department_id) { return this.get("/polls/today", { department_id }); },
  polls(department_id) { return this.get("/polls", { department_id }); },
  generatePoll(payload) { return this.post("/polls/generate", payload); },
  vote(pollId, option_id) { return this.post(`/polls/${pollId}/vote`, { option_id }); },

  // ---- Discussions
  discussions(department_id, sort) { return this.get("/discussions", { department_id, sort }); },
  createDiscussion(payload) { return this.post("/discussions", payload); },
  likeDiscussion(id) { return this.post(`/discussions/${id}/like`); },
  deleteDiscussion(id) { return this.del(`/discussions/${id}`); },
  comments(discussionId) { return this.get(`/discussions/${discussionId}/comments`); },
  addComment(discussionId, content) { return this.post(`/discussions/${discussionId}/comments`, { content }); },

  // ---- Quizzes
  todayQuiz(department_id) { return this.get("/quizzes/today", { department_id }); },
  generateQuiz(payload) { return this.post("/quizzes/generate", payload); },
  submitQuiz(quizId, answers) { return this.post(`/quizzes/${quizId}/submit`, { answers }); },

  // ---- Notifications
  notifications() { return this.get("/notifications"); },
  markNotificationRead(id) { return this.post(`/notifications/${id}/read`); },

  // ---- Leaderboard / Analytics
  leaderboard(department_id, limit) { return this.get("/leaderboard", { department_id, limit }); },
  analyticsOverview() { return this.get("/analytics/overview"); },
  departmentEngagement() { return this.get("/analytics/department-engagement"); },
  weeklyActivity() { return this.get("/analytics/weekly-activity"); },

  // ---- Employees / Admin
  employees(params) { return this.get("/employees", params); },
  createEmployee(payload) { return this.post("/employees", payload); },
  updateEmployee(id, payload) { return this.put(`/employees/${id}`, payload); },
  deleteEmployee(id) { return this.del(`/employees/${id}`); },
  createDepartment(payload) { return this.post("/departments", payload); },
  deleteDepartment(id) { return this.del(`/departments/${id}`); },

  // ---- Search
  search(q) { return this.get("/search", { q }); },

  // ---- Chatbot
  chat(message, history) { return this.post("/chatbot/message", { message, history }); },

  // ---- Daily content
  dailyTip(department_id) { return this.get("/daily/tip", { department_id }); },
  dailyQuestion(department_id) { return this.get("/daily/discussion-question", { department_id }); },
};
