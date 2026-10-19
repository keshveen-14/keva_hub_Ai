(async function init() {
  await KevaApp.mount("analytics");
  const user = KevaAPI.currentUser();
  if (!user || user.role !== "admin") {
    KevaApp.toast("Admin access required", "error");
    window.location.href = "dashboard.html";
    return;
  }

  loadStats();
  loadWeekly();
  loadDeptEngagement();
})();

function isDark() { return document.documentElement.getAttribute("data-theme") === "dark"; }
function gridColor() { return isDark() ? "#2A2F45" : "#E3E7F0"; }
function textColor() { return isDark() ? "#A7ADC2" : "#6B7280"; }

async function loadStats() {
  const el = document.getElementById("anStats");
  try {
    const o = await KevaAPI.analyticsOverview();
    const cards = [
      { label: "Total Employees", value: o.total_employees, icon: "fa-users", color: "var(--kv-primary)", bg: "var(--kv-primary-light)" },
      { label: "Active This Week", value: o.active_this_week, icon: "fa-user-check", color: "#0E9F7E", bg: "#E4F8F3" },
      { label: "Poll Participation", value: o.total_votes, icon: "fa-square-poll-vertical", color: "#C97A16", bg: "#FFF3E0" },
      { label: "Discussion Activity", value: `${o.total_discussions} / ${o.total_comments}`, icon: "fa-comments", color: "#D9483F", bg: "#FDEEEC" },
      { label: "Quiz Attempts", value: o.total_quiz_attempts, icon: "fa-circle-question", color: "#7C4DCC", bg: "#F2EBFB" },
      { label: "Posters Published", value: o.total_posters, icon: "fa-image", color: "#0E7FC9", bg: "#E6F4FF" },
    ];
    el.innerHTML = cards.map(c => `
      <div class="col-6 col-lg-2">
        <div class="kv-card kv-stat-card">
          <div class="icon" style="background:${c.bg};color:${c.color};"><i class="fa-solid ${c.icon}"></i></div>
          <div class="num" style="font-size:20px;">${c.value}</div>
          <div class="label">${c.label}</div>
        </div>
      </div>`).join("");
  } catch (e) { el.innerHTML = ""; }
}

async function loadWeekly() {
  try {
    const w = await KevaAPI.weeklyActivity();
    new Chart(document.getElementById("weeklyChart"), {
      type: "line",
      data: {
        labels: w.labels,
        datasets: [
          { label: "Discussions", data: w.discussions, borderColor: "#2952E3", backgroundColor: "rgba(41,82,227,.1)", tension: .35, fill: true },
          { label: "Comments", data: w.comments, borderColor: "#00B8A9", backgroundColor: "rgba(0,184,169,.1)", tension: .35, fill: true },
          { label: "Votes", data: w.votes, borderColor: "#C97A16", backgroundColor: "rgba(201,122,22,.1)", tension: .35, fill: true },
        ],
      },
      options: {
        plugins: { legend: { labels: { color: textColor() } } },
        scales: {
          x: { grid: { color: gridColor() }, ticks: { color: textColor() } },
          y: { grid: { color: gridColor() }, ticks: { color: textColor() }, beginAtZero: true },
        },
      },
    });
  } catch (e) { /* silent */ }
}

async function loadDeptEngagement() {
  try {
    const rows = await KevaAPI.departmentEngagement();
    new Chart(document.getElementById("deptChart"), {
      type: "bar",
      data: {
        labels: rows.map(r => r.department),
        datasets: [{ label: "Discussions", data: rows.map(r => r.discussions), backgroundColor: "#2952E3", borderRadius: 6 }],
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: gridColor() }, ticks: { color: textColor() }, beginAtZero: true },
          y: { grid: { display: false }, ticks: { color: textColor() } },
        },
      },
    });

    document.getElementById("anDeptTable").innerHTML = rows.map(r => `
      <tr>
        <td class="ps-3">${r.department}</td>
        <td>${r.employees}</td>
        <td>${r.discussions}</td>
        <td>${r.polls}</td>
        <td>${r.votes}</td>
      </tr>`).join("");
  } catch (e) { /* silent */ }
}
