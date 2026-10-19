(async function init() {
  await KevaApp.mount("profile");
  const user = await KevaAPI.me();
  KevaAPI.setCurrentUser(user);

  document.getElementById("pfAvatar").textContent = KevaApp.initials(user.name);
  document.getElementById("pfName").textContent = user.name;
  document.getElementById("pfDesignation").textContent = user.designation || "Employee";
  const deptChip = document.getElementById("pfDept");
  deptChip.textContent = KevaApp.depName(user.department_id);
  deptChip.className = `dep-chip mt-2 d-inline-flex ${KevaApp.depClass(user.department_id)}`;
  document.getElementById("pfPoints").textContent = user.points || 0;
  document.getElementById("pfStreak").textContent = user.streak_days || 0;

  document.getElementById("pfDetails").innerHTML = `
    <div class="d-flex justify-content-between"><span class="text-muted">Employee ID</span><strong>${user.employee_code || "—"}</strong></div>
    <div class="d-flex justify-content-between"><span class="text-muted">Email</span><strong>${user.email}</strong></div>
    <div class="d-flex justify-content-between"><span class="text-muted">Experience</span><strong>${user.experience_years || 0} yrs</strong></div>
    <div class="d-flex justify-content-between"><span class="text-muted">Manager</span><strong>${user.manager || "—"}</strong></div>
    <div class="d-flex justify-content-between"><span class="text-muted">Joined</span><strong>${user.join_date ? new Date(user.join_date + "Z").toLocaleDateString() : "—"}</strong></div>
    <div class="d-flex justify-content-between"><span class="text-muted">Status</span><strong style="text-transform:capitalize;">${user.status}</strong></div>
  `;

  loadBookmarks();
  renderBadges(user);
})();

async function loadBookmarks() {
  const el = document.getElementById("pfBookmarks");
  try {
    const posters = await KevaAPI.myBookmarks();
    if (!posters.length) { el.innerHTML = `<div class="kv-empty"><i class="fa-regular fa-bookmark"></i>No bookmarked posters yet.</div>`; return; }
    el.innerHTML = `<div class="row g-3">` + posters.map(p => `
      <div class="col-md-6">
        <div class="kv-card kv-card-pad">
          <div style="font-weight:700;font-size:13.5px;">${p.title}</div>
          <div style="font-size:12.3px;color:var(--kv-text-muted);margin-top:4px;">${(p.explanation || "").slice(0, 90)}...</div>
        </div>
      </div>`).join("") + `</div>`;
  } catch (e) { el.innerHTML = `<div class="kv-empty"><i class="fa-solid fa-triangle-exclamation"></i>Couldn't load bookmarks.</div>`; }
}

function renderBadges(user) {
  const points = user.points || 0;
  const badges = [
    { name: "First Steps", icon: "fa-shoe-prints", earned: points >= 5, desc: "Logged in for the first time" },
    { name: "Voter", icon: "fa-square-poll-vertical", earned: points >= 10, desc: "Cast your first poll vote" },
    { name: "Conversationalist", icon: "fa-comments", earned: points >= 20, desc: "Started a discussion" },
    { name: "Quiz Whiz", icon: "fa-brain", earned: points >= 40, desc: "Completed an AI quiz" },
    { name: "Rising Star", icon: "fa-star", earned: points >= 75, desc: "Reached 75 learning points" },
    { name: "AI Champion", icon: "fa-crown", earned: points >= 150, desc: "Reached 150 learning points" },
  ];
  document.getElementById("pfBadges").innerHTML = `<div class="row g-3">` + badges.map(b => `
    <div class="col-6 col-md-4">
      <div class="kv-card kv-card-pad text-center" style="opacity:${b.earned ? 1 : .4};">
        <div class="icon mx-auto" style="width:44px;height:44px;border-radius:12px;background:${b.earned ? 'var(--kv-signal-light)' : 'var(--kv-surface-alt)'};color:${b.earned ? 'var(--kv-signal)' : 'var(--kv-text-faint)'};display:flex;align-items:center;justify-content:center;font-size:17px;margin-bottom:8px;">
          <i class="fa-solid ${b.icon}"></i>
        </div>
        <div style="font-weight:700;font-size:12.5px;">${b.name}</div>
        <div style="font-size:10.8px;color:var(--kv-text-muted);">${b.desc}</div>
      </div>
    </div>`).join("") + `</div>`;
}
