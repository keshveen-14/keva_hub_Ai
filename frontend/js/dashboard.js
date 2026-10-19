(async function init() {
  await KevaApp.mount("dashboard");

  const user = KevaAPI.currentUser();
  const params = new URLSearchParams(window.location.search);
  const departmentId = params.get("department_id") ? parseInt(params.get("department_id")) : (user?.department_id || null);

  document.getElementById("kvGreeting").textContent = `Welcome back, ${user?.name?.split(" ")[0] || "there"} 👋`;
  document.getElementById("kvDeptEyebrow").textContent = departmentId ? KevaApp.depName(departmentId) : "All Departments";

  if (user?.role === "admin") {
    const el = document.getElementById("kvAdminQuickActions");
    el.style.setProperty("display", "flex", "important");
    el.innerHTML = `
      <button class="btn btn-kv-soft" onclick="genPoster(${departmentId || 'null'})"><i class="fa-solid fa-wand-magic-sparkles me-1"></i>Generate Poster</button>
      <button class="btn btn-kv-soft" onclick="genPoll(${departmentId || 'null'})"><i class="fa-solid fa-wand-magic-sparkles me-1"></i>Generate Poll</button>
    `;
  }

  loadStats(departmentId);
  loadPoster(departmentId);
  loadPoll(departmentId);
  loadDiscussions(departmentId);
  loadTip(departmentId);
  loadLeaderboard(departmentId);
  loadActivity(departmentId);
})();

async function loadStats(departmentId) {
  const el = document.getElementById("kvQuickStats");
  try {
    const [posters, polls, discussions] = await Promise.all([
      KevaAPI.posters(departmentId), KevaAPI.polls(departmentId), KevaAPI.discussions(departmentId),
    ]);
    const user = KevaAPI.currentUser();
    const stats = [
      { icon: "fa-image", color: "var(--kv-primary)", bg: "var(--kv-primary-light)", num: posters.length, label: "Posters Published" },
      { icon: "fa-square-poll-vertical", color: "#0E9F7E", bg: "#E4F8F3", num: polls.length, label: "Polls Run" },
      { icon: "fa-comments", color: "#D9483F", bg: "#FDEEEC", num: discussions.length, label: "Discussions" },
      { icon: "fa-star", color: "#C97A16", bg: "#FFF3E0", num: user?.points || 0, label: "Your Points" },
    ];
    el.innerHTML = stats.map(s => `
      <div class="col-6 col-lg-3">
        <div class="kv-card kv-stat-card">
          <div class="icon" style="background:${s.bg};color:${s.color};"><i class="fa-solid ${s.icon}"></i></div>
          <div class="num">${s.num}</div>
          <div class="label">${s.label}</div>
        </div>
      </div>`).join("");
  } catch (e) { el.innerHTML = ""; }
}

async function loadPoster(departmentId) {
  const el = document.getElementById("kvPosterArea");
  try {
    const poster = await KevaAPI.todayPoster(departmentId);
    if (!poster) { el.innerHTML = emptyState("fa-image", "No poster yet for this department."); return; }
    el.innerHTML = renderPoster(poster);
  } catch (e) { el.innerHTML = emptyState("fa-triangle-exclamation", "Couldn't load today's poster."); }
}

function renderPoster(poster) {
  const keyPoints = (poster.key_points || "").split("\n").filter(Boolean);
  return `
    <div class="kv-poster-banner mb-3">
      <i class="fa-solid fa-wand-magic-sparkles kv-poster-icon"></i>
      <div class="kv-poster-title">${poster.title}</div>
    </div>
    <p style="font-size:14px;">${poster.explanation || ""}</p>
    <div class="row g-3">
      <div class="col-md-6 kv-poster-section">
        <h6>Key Points</h6>
        <ul class="ps-3 mb-0">${keyPoints.map(k => `<li>${k.replace(/^•\s*/, "")}</li>`).join("")}</ul>
      </div>
      <div class="col-md-6 kv-poster-section">
        <h6>Real-World Use Case</h6>
        <p>${poster.real_world_use_case || "—"}</p>
      </div>
      <div class="col-md-6 kv-poster-section">
        <h6>Best Practices</h6>
        <p>${poster.best_practices || "—"}</p>
      </div>
      <div class="col-md-6 kv-poster-section">
        <h6>Example</h6>
        <p>${poster.example || "—"}</p>
      </div>
      <div class="col-12 kv-poster-section">
        <h6>Applications</h6>
        <p>${poster.applications || "—"}</p>
      </div>
    </div>
    <button class="btn btn-kv-outline btn-sm mt-2" onclick="toggleBookmark(${poster.id}, this)"><i class="fa-regular fa-bookmark me-1"></i>Bookmark</button>
  `;
}

async function toggleBookmark(posterId, btn) {
  try {
    const res = await KevaAPI.bookmarkPoster(posterId);
    btn.innerHTML = res.bookmarked ? `<i class="fa-solid fa-bookmark me-1"></i>Bookmarked` : `<i class="fa-regular fa-bookmark me-1"></i>Bookmark`;
    KevaApp.toast(res.bookmarked ? "Poster bookmarked" : "Bookmark removed");
  } catch (e) { KevaApp.toast(e.message, "error"); }
}

async function loadPoll(departmentId) {
  const el = document.getElementById("kvPollArea");
  try {
    const poll = await KevaAPI.todayPoll(departmentId);
    if (!poll) { el.innerHTML = emptyState("fa-square-poll-vertical", "No poll yet for this department."); return; }
    el.innerHTML = renderPoll(poll);
  } catch (e) { el.innerHTML = emptyState("fa-triangle-exclamation", "Couldn't load today's poll."); }
}

function renderPoll(poll) {
  const total = poll.total_votes || 0;
  const voted = poll.my_vote_option_id != null;
  const optionsHtml = poll.options.map(o => {
    const pct = total ? Math.round((o.votes / total) * 100) : 0;
    return `
      <div class="kv-poll-option ${voted ? 'voted' : ''} ${poll.my_vote_option_id === o.id ? 'mine' : ''}" ${voted ? '' : `onclick="castVote(${poll.id}, ${o.id})"`}>
        ${voted ? `<div class="fill" style="width:${pct}%;"></div>` : ""}
        <div class="row-content">
          <span>${o.text}</span>
          ${voted ? `<span>${pct}% (${o.votes})</span>` : `<i class="fa-regular fa-circle" style="color:var(--kv-text-faint)"></i>`}
        </div>
      </div>`;
  }).join("");
  return `
    <p style="font-weight:700;font-size:15px;margin-bottom:14px;">${poll.question}</p>
    <div id="kvPollOptions">${optionsHtml}</div>
    <div class="text-muted mt-2" style="font-size:12px;">${total} vote${total !== 1 ? "s" : ""} total ${voted ? "· thanks for voting!" : "· tap an option to vote"}</div>
  `;
}

async function castVote(pollId, optionId) {
  try {
    const poll = await KevaAPI.vote(pollId, optionId);
    document.getElementById("kvPollArea").innerHTML = renderPoll(poll);
    KevaApp.toast("Vote recorded — +2 points");
    loadStats(new URLSearchParams(window.location.search).get("department_id"));
  } catch (e) { KevaApp.toast(e.message, "error"); }
}

async function loadDiscussions(departmentId) {
  const el = document.getElementById("kvDiscussionsArea");
  try {
    const discussions = (await KevaAPI.discussions(departmentId, "latest")).slice(0, 4);
    if (!discussions.length) { el.innerHTML = emptyState("fa-comments", "No discussions yet. Start one!"); return; }
    el.innerHTML = discussions.map(d => `
      <div class="kv-discussion">
        <div class="d-flex justify-content-between">
          <div class="d-title">${d.title}</div>
          <span class="dep-chip ${KevaApp.depClass(d.department_id)}">${KevaApp.depName(d.department_id)}</span>
        </div>
        <div class="d-meta">${d.author_name} · ${KevaApp.timeAgo(d.created_at)}</div>
        <div class="d-content">${(d.content || "").slice(0, 140)}${d.content && d.content.length > 140 ? "…" : ""}</div>
        <div class="d-actions">
          <span><i class="fa-regular fa-heart"></i> ${d.likes_count}</span>
          <span><i class="fa-regular fa-comment"></i> ${d.comments_count}</span>
        </div>
      </div>`).join("");
  } catch (e) { el.innerHTML = emptyState("fa-triangle-exclamation", "Couldn't load discussions."); }
}

async function loadTip(departmentId) {
  const el = document.getElementById("kvTipArea");
  try {
    const res = await KevaAPI.dailyTip(departmentId);
    el.textContent = res.tip;
  } catch (e) { el.textContent = "Check back later for today's tip."; }
}

async function loadLeaderboard(departmentId) {
  const el = document.getElementById("kvLeaderboardArea");
  try {
    const rows = await KevaAPI.leaderboard(departmentId, 5);
    if (!rows.length) { el.innerHTML = emptyState("fa-trophy", "No activity yet."); return; }
    el.innerHTML = rows.map(r => `
      <div class="kv-leader-row">
        <div class="kv-leader-rank">${r.rank}</div>
        <div class="kv-avatar" style="width:28px;height:28px;font-size:11px;">${KevaApp.initials(r.name)}</div>
        <div>
          <div style="font-size:13px;font-weight:600;">${r.name}</div>
          <div style="font-size:11px;color:var(--kv-text-muted);">${r.department || ""}</div>
        </div>
        <div class="kv-leader-points">${r.points} pts</div>
      </div>`).join("");
  } catch (e) { el.innerHTML = ""; }
}

async function loadActivity(departmentId) {
  const el = document.getElementById("kvActivityArea");
  try {
    const notes = (await KevaAPI.notifications()).slice(0, 5);
    if (!notes.length) { el.innerHTML = emptyState("fa-clock-rotate-left", "No recent activity."); return; }
    el.innerHTML = notes.map(n => `
      <div class="d-flex gap-2 mb-3">
        <i class="fa-solid ${iconFor(n.type)}" style="color:var(--kv-primary);margin-top:2px;"></i>
        <div>
          <div style="font-size:12.8px;font-weight:600;">${n.title}</div>
          <div style="font-size:11.5px;color:var(--kv-text-muted);">${KevaApp.timeAgo(n.created_at)}</div>
        </div>
      </div>`).join("");
  } catch (e) { el.innerHTML = ""; }
}

function iconFor(type) {
  return { poster: "fa-image", poll: "fa-square-poll-vertical", reply: "fa-reply", announcement: "fa-bullhorn" }[type] || "fa-bell";
}

function emptyState(icon, text) {
  return `<div class="kv-empty"><i class="fa-solid ${icon}"></i>${text}</div>`;
}

async function genPoster(departmentId) {
  try {
    KevaApp.toast("Generating AI poster...");
    await KevaAPI.generatePoster({ department_id: departmentId });
    loadPoster(departmentId); loadStats(departmentId);
    KevaApp.toast("New poster generated!");
  } catch (e) { KevaApp.toast(e.message, "error"); }
}

async function genPoll(departmentId) {
  try {
    KevaApp.toast("Generating AI poll...");
    await KevaAPI.generatePoll({ department_id: departmentId });
    loadPoll(departmentId); loadStats(departmentId);
    KevaApp.toast("New poll generated!");
  } catch (e) { KevaApp.toast(e.message, "error"); }
}
