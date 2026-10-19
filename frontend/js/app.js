/* Shared app shell used across every authenticated page:
   sidebar + department list, topbar (search/notifications/user),
   dark mode, and the floating AI chatbot widget. */

const KevaApp = {
  departments: [],
  currentDeptId: null,

  depClass(depId) {
    if (!this.departments.length) return "dep-0";
    const idx = this.departments.findIndex(d => d.id === depId);
    return `dep-${((idx < 0 ? 0 : idx) % 10)}`;
  },

  depName(depId) {
    const d = this.departments.find(x => x.id === depId);
    return d ? d.name : "General";
  },

  initials(name) {
    if (!name) return "?";
    return name.split(" ").filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join("");
  },

  timeAgo(iso) {
    const diff = (Date.now() - new Date(iso + "Z").getTime()) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  },

  requireAuth() {
    if (!KevaAPI.token()) {
      window.location.href = "index.html";
      return false;
    }
    return true;
  },

  applyTheme() {
    const theme = localStorage.getItem("keva_theme") || "light";
    document.documentElement.setAttribute("data-theme", theme);
  },

  toggleTheme() {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    const next = cur === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("keva_theme", next);
  },

  async mount(activeNav) {
    this.applyTheme();
    if (!this.requireAuth()) return;

    const user = KevaAPI.currentUser();
    if (!user) {
      try { const me = await KevaAPI.me(); KevaAPI.setCurrentUser(me); } catch (e) { return; }
    }

    try { this.departments = await KevaAPI.departments(); } catch (e) { this.departments = []; }

    this.renderSidebar(activeNav);
    this.renderTopbar();
    this.renderChatbot();
    this.loadNotifications();
    this.wireGlobalSearch();
  },

  renderSidebar(activeNav) {
    const user = KevaAPI.currentUser();
    const isAdmin = user && user.role === "admin";
    const urlParams = new URLSearchParams(window.location.search);
    const selectedDept = urlParams.get("department_id");

    const depLinks = this.departments.map((d, i) => `
      <div class="kv-dept-link ${String(d.id) === selectedDept ? 'active' : ''}" onclick="KevaApp.goDept(${d.id})">
        <span class="dot dep-${i % 10}" style="background:currentColor;opacity:.85"></span>
        <span>${d.name}</span>
      </div>`).join("");

    const html = `
      <div class="kv-sidebar-brand">
        <div class="kv-logo-mark">K</div>
        <div class="kv-brand-text">
          <strong>KEVA AI Hub</strong>
          <span>Learning Portal</span>
        </div>
      </div>
      <div class="kv-sidebar-scroll kv-scroll-thin">
        <div class="kv-nav-link ${activeNav === 'dashboard' ? 'active' : ''}" onclick="location.href='dashboard.html'">
          <i class="fa-solid fa-grid-2"></i> Dashboard
        </div>
        <div class="kv-nav-link ${activeNav === 'discussions' ? 'active' : ''}" onclick="location.href='discussions.html'">
          <i class="fa-solid fa-comments"></i> Discussions
        </div>
        <div class="kv-nav-link ${activeNav === 'quiz' ? 'active' : ''}" onclick="location.href='quiz.html'">
          <i class="fa-solid fa-circle-question"></i> AI Quiz
        </div>
        <div class="kv-nav-link ${activeNav === 'leaderboard' ? 'active' : ''}" onclick="location.href='leaderboard.html'">
          <i class="fa-solid fa-trophy"></i> Leaderboard
        </div>
        <div class="kv-nav-link ${activeNav === 'profile' ? 'active' : ''}" onclick="location.href='profile.html'">
          <i class="fa-solid fa-user"></i> My Profile
        </div>

        <div class="kv-nav-section-title">Departments</div>
        <div class="kv-dept-link ${!selectedDept ? 'active' : ''}" onclick="KevaApp.goDept(null)">
          <span class="dot" style="background:var(--kv-text-faint)"></span><span>All Departments</span>
        </div>
        ${depLinks}

        ${isAdmin ? `
        <div class="kv-nav-section-title">Admin</div>
        <div class="kv-nav-link ${activeNav === 'admin' ? 'active' : ''}" onclick="location.href='admin.html'">
          <i class="fa-solid fa-user-gear"></i> Manage Employees
        </div>
        <div class="kv-nav-link ${activeNav === 'analytics' ? 'active' : ''}" onclick="location.href='analytics.html'">
          <i class="fa-solid fa-chart-pie"></i> Analytics
        </div>` : ""}
      </div>
    `;
    document.querySelectorAll(".kv-sidebar").forEach(el => el.innerHTML = html);
  },

  goDept(id) {
    const page = window.location.pathname.split("/").pop() || "dashboard.html";
    window.location.href = id ? `${page}?department_id=${id}` : page.split("?")[0];
  },

  renderTopbar() {
    const user = KevaAPI.currentUser();
    document.querySelectorAll(".kv-topbar-user").forEach(el => {
      el.innerHTML = `
        <div class="kv-avatar">
        <img src="${user?.profile_picture || '/assets/default-avatar.png'}"alt="Profile"
      style="width:100%;height:100%;object-fit:cover;border-radius:50%;">
      </div>
          <div class="name">${user?.name || ""}</div>
          <div class="role">${user?.role === 'admin' ? 'Administrator' : (user?.designation || 'Employee')}</div>
        </div>
        <i class="fa-solid fa-chevron-down" style="font-size:10px;color:var(--kv-text-faint)"></i>
      `;
    });
  },

  logout() {
    KevaAPI.clearSession();
    window.location.href = "index.html";
  },

  toggleUserMenu() {
    const menu = document.getElementById("kvUserMenu");
    if (menu) menu.classList.toggle("open");
  },

  toggleSidebar() {
    document.querySelectorAll(".kv-sidebar").forEach(el => el.classList.toggle("open"));
  },

  async loadNotifications() {
    try {
      const notes = await KevaAPI.notifications();
      const unread = notes.filter(n => !n.is_read).length;
      const badge = document.getElementById("kvNotifBadge");
      if (badge) {
        badge.style.display = unread ? "flex" : "none";
        badge.textContent = unread > 9 ? "9+" : unread;
      }
      const panel = document.getElementById("kvNotifPanel");
      if (panel) {
        panel.innerHTML = notes.length ? notes.map(n => `
          <div class="kv-notif-item">
            <div class="t">${n.title}</div>
            <div class="m">${n.message}</div>
            <div class="ts">${this.timeAgo(n.created_at)}</div>
          </div>`).join("") : `<div class="kv-empty" style="padding:24px"><i class="fa-regular fa-bell-slash"></i>No notifications yet</div>`;
      }
    } catch (e) { /* silent */ }
  },

  toggleNotifPanel() {
    document.getElementById("kvNotifPanel")?.classList.toggle("open");
  },

  wireGlobalSearch() {
    const input = document.getElementById("kvGlobalSearch");
    if (!input) return;
    let t;
    input.addEventListener("input", () => {
      clearTimeout(t);
      const q = input.value.trim();
      t = setTimeout(() => { if (q.length >= 2) this.runSearch(q); else this.hideSearchResults(); }, 350);
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest("#kvGlobalSearchWrap")) this.hideSearchResults();
    });
  },

  hideSearchResults() {
    const el = document.getElementById("kvSearchResults");
    if (el) el.classList.remove("open");
  },

  async runSearch(q) {
    try {
      const res = await KevaAPI.search(q);
      const el = document.getElementById("kvSearchResults");
      if (!el) return;
      const rows = [];
      res.employees.forEach(e => rows.push(`<div class="kv-notif-item"><i class="fa-solid fa-user me-2"></i>${e.name} <span class="m">— ${e.designation || ''}</span></div>`));
      res.posters.forEach(p => rows.push(`<div class="kv-notif-item"><i class="fa-solid fa-image me-2"></i>${p.title}</div>`));
      res.polls.forEach(p => rows.push(`<div class="kv-notif-item"><i class="fa-solid fa-square-poll-vertical me-2"></i>${p.question}</div>`));
      res.discussions.forEach(d => rows.push(`<div class="kv-notif-item"><i class="fa-solid fa-comments me-2"></i>${d.title}</div>`));
      el.innerHTML = rows.length ? rows.join("") : `<div class="kv-empty" style="padding:20px"><i class="fa-solid fa-magnifying-glass"></i>No results for "${q}"</div>`;
      el.classList.add("open");
    } catch (e) { /* silent */ }
  },

  // ------------------------------------------------------------ Chatbot
  chatHistory: [],

  renderChatbot() {
    if (document.getElementById("kvChatFab")) return;
    const fab = document.createElement("button");
    fab.id = "kvChatFab";
    fab.className = "kv-chat-fab";
    fab.innerHTML = `<i class="fa-solid fa-robot"></i>`;
    fab.onclick = () => document.getElementById("kvChatWindow").classList.toggle("open");
    document.body.appendChild(fab);

    const win = document.createElement("div");
    win.id = "kvChatWindow";
    win.className = "kv-chat-window";
    win.innerHTML = `
      <div class="kv-chat-header">
        <i class="fa-solid fa-robot"></i>
        <div>
          <div style="font-weight:700;font-size:13.5px;">KEVA Assistant</div>
          <div style="font-size:11px;opacity:.85;">Ask me anything about AI</div>
        </div>
        <i class="fa-solid fa-xmark ms-auto" style="cursor:pointer" onclick="document.getElementById('kvChatWindow').classList.remove('open')"></i>
      </div>
      <div class="kv-chat-body kv-scroll-thin" id="kvChatBody">
        <div class="kv-chat-msg bot">Hi! I'm KEVA 👋 Ask me about AI concepts, today's poster, or how to use the hub.</div>
      </div>
      <div class="kv-chat-input">
        <input id="kvChatInput" type="text" placeholder="Type a message..." onkeydown="if(event.key==='Enter')KevaApp.sendChat()"/>
        <button onclick="KevaApp.sendChat()"><i class="fa-solid fa-paper-plane"></i></button>
      </div>
    `;
    document.body.appendChild(win);
  },

  async sendChat() {
    const input = document.getElementById("kvChatInput");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    const body = document.getElementById("kvChatBody");
    body.insertAdjacentHTML("beforeend", `<div class="kv-chat-msg user">${msg}</div>`);
    body.scrollTop = body.scrollHeight;
    this.chatHistory.push({ role: "user", content: msg });

    body.insertAdjacentHTML("beforeend", `<div class="kv-chat-msg bot" id="kvChatTyping">Typing...</div>`);
    body.scrollTop = body.scrollHeight;

    try {
      const res = await KevaAPI.chat(msg, this.chatHistory);
      document.getElementById("kvChatTyping")?.remove();
      body.insertAdjacentHTML("beforeend", `<div class="kv-chat-msg bot">${res.reply}</div>`);
      this.chatHistory.push({ role: "assistant", content: res.reply });
    } catch (e) {
      document.getElementById("kvChatTyping")?.remove();
      body.insertAdjacentHTML("beforeend", `<div class="kv-chat-msg bot">Sorry, I couldn't reach the assistant right now.</div>`);
    }
    body.scrollTop = body.scrollHeight;
  },

  toast(message, type = "success") {
    const el = document.createElement("div");
    el.className = "position-fixed top-0 end-0 m-3 p-3 rounded-3 shadow";
    el.style.cssText = `z-index:2000;background:${type === 'error' ? '#E5484D' : '#12B76A'};color:#fff;font-size:13.5px;font-weight:600;max-width:320px;`;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  },
};
