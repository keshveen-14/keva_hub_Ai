(async function init() {
  await KevaApp.mount("leaderboard");
  const params = new URLSearchParams(window.location.search);
  const deptId = params.get("department_id") ? parseInt(params.get("department_id")) : null;
  document.getElementById("kvDeptEyebrow").textContent = deptId ? KevaApp.depName(deptId) : "Leaderboard · All Departments";

  try {
    const rows = await KevaAPI.leaderboard(deptId, 20);
    renderPodium(rows.slice(0, 3));
    renderList(rows);
  } catch (e) {
    document.getElementById("kvLeaderList").innerHTML = `<div class="kv-empty"><i class="fa-solid fa-triangle-exclamation"></i>Couldn't load the leaderboard.</div>`;
  }
})();

function renderPodium(top3) {
  const el = document.getElementById("kvPodium");
  if (!top3.length) { el.innerHTML = ""; return; }
  const order = [1, 0, 2].filter(i => top3[i]);
  const colors = ["#B4780C", "#2952E3", "#B25522"];
  el.innerHTML = order.map(i => {
    const r = top3[i];
    const height = i === 0 ? 150 : (i === 1 ? 190 : 120);
    return `
      <div class="col-4 d-flex flex-column align-items-center justify-content-end">
        <div class="kv-avatar mb-2" style="width:52px;height:52px;font-size:16px;border:3px solid ${colors[i]};">${KevaApp.initials(r.name)}</div>
        <div style="font-weight:700;font-size:13.5px;text-align:center;">${r.name}</div>
        <div style="font-size:11.5px;color:var(--kv-text-muted);margin-bottom:8px;">${r.points} pts</div>
        <div class="kv-card" style="width:100%;height:${height}px;display:flex;align-items:flex-start;justify-content:center;padding-top:10px;background:${colors[i]}1A;border-color:${colors[i]}44;">
          <span style="font-family:var(--kv-font-display);font-size:26px;font-weight:800;color:${colors[i]};">#${r.rank}</span>
        </div>
      </div>`;
  }).join("");
}

function renderList(rows) {
  const el = document.getElementById("kvLeaderList");
  if (!rows.length) { el.innerHTML = `<div class="kv-empty"><i class="fa-solid fa-trophy"></i>No leaderboard activity yet.</div>`; return; }
  const me = KevaAPI.currentUser();
  el.innerHTML = rows.map(r => `
    <div class="kv-leader-row" style="${me && me.id === r.employee_id ? 'background:var(--kv-primary-light);border-radius:10px;padding-left:8px;padding-right:8px;' : ''}">
      <div class="kv-leader-rank">${r.rank}</div>
      <div class="kv-avatar" style="width:30px;height:30px;font-size:11.5px;">${KevaApp.initials(r.name)}</div>
      <div>
        <div style="font-size:13.5px;font-weight:600;">${r.name} ${me && me.id === r.employee_id ? '<span style="color:var(--kv-primary);font-size:11px;">(you)</span>' : ''}</div>
        <div style="font-size:11.5px;color:var(--kv-text-muted);">${r.department || ""}</div>
      </div>
      <div class="kv-leader-points">${r.points} pts</div>
    </div>`).join("");
}
