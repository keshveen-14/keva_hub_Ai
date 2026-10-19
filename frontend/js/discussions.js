let kvDeptId = null;
let kvSort = "latest";
let kvActiveDiscussion = null;

(async function init() {
  await KevaApp.mount("discussions");
  const params = new URLSearchParams(window.location.search);
  kvDeptId = params.get("department_id") ? parseInt(params.get("department_id")) : null;
  document.getElementById("kvDeptEyebrow").textContent = kvDeptId ? KevaApp.depName(kvDeptId) : "Community · All Departments";

  const sel = document.getElementById("ndDept");
  sel.innerHTML = `<option value="">General</option>` + KevaApp.departments.map(d => `<option value="${d.id}" ${d.id === kvDeptId ? "selected" : ""}>${d.name}</option>`).join("");

  loadList();
  loadQuestion();
})();

function setSort(sort, btn) {
  kvSort = sort;
  document.querySelectorAll("#sortTabs .nav-link").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");
  loadList();
}

async function loadQuestion() {
  try {
    const res = await KevaAPI.dailyQuestion(kvDeptId);
    document.getElementById("kvQuestionArea").textContent = res.question;
  } catch (e) { /* silent */ }
}

async function loadList() {
  const el = document.getElementById("kvDiscussionList");
  try {
    const discussions = await KevaAPI.discussions(kvDeptId, kvSort);
    if (!discussions.length) {
      el.innerHTML = `<div class="kv-empty"><i class="fa-solid fa-comments"></i>No discussions yet — be the first to start one!</div>`;
      return;
    }
    el.innerHTML = discussions.map(d => `
      <div class="kv-discussion">
        <div class="d-flex justify-content-between align-items-start">
          <div class="d-title" style="cursor:pointer;" onclick="openDiscussion(${d.id})">${d.title}</div>
          <span class="dep-chip ${KevaApp.depClass(d.department_id)}">${KevaApp.depName(d.department_id)}</span>
        </div>
        <div class="d-meta">${d.author_name} · ${KevaApp.timeAgo(d.created_at)}</div>
        <div class="d-content">${d.content}</div>
        ${d.image_url ? `<img src="${d.image_url}" style="max-width:100%;border-radius:10px;margin-bottom:10px;" onerror="this.style.display='none'">` : ""}
        <div class="d-actions">
          <span class="${d.liked_by_me ? 'liked' : ''}" onclick="likeDiscussion(${d.id}, this)"><i class="fa-${d.liked_by_me ? 'solid' : 'regular'} fa-heart"></i> ${d.likes_count}</span>
          <span onclick="openDiscussion(${d.id})"><i class="fa-regular fa-comment"></i> ${d.comments_count}</span>
        </div>
      </div>`).join("");
  } catch (e) { el.innerHTML = `<div class="kv-empty"><i class="fa-solid fa-triangle-exclamation"></i>Couldn't load discussions.</div>`; }
}

async function likeDiscussion(id, el) {
  try {
    const res = await KevaAPI.likeDiscussion(id);
    el.classList.toggle("liked", res.liked);
    el.innerHTML = `<i class="fa-${res.liked ? 'solid' : 'regular'} fa-heart"></i> ${res.likes_count}`;
  } catch (e) { KevaApp.toast(e.message, "error"); }
}

async function submitDiscussion(e) {
  e.preventDefault();
  try {
    const payload = {
      title: document.getElementById("ndTitle").value,
      content: document.getElementById("ndContent").value,
      department_id: document.getElementById("ndDept").value ? parseInt(document.getElementById("ndDept").value) : null,
      image_url: document.getElementById("ndImage").value || null,
    };
    await KevaAPI.createDiscussion(payload);
    bootstrap.Modal.getInstance(document.getElementById("newDiscussionModal")).hide();
    document.getElementById("newDiscussionForm").reset();
    KevaApp.toast("Discussion posted — +4 points");
    loadList();
  } catch (err) { KevaApp.toast(err.message, "error"); }
  return false;
}

async function openDiscussion(id) {
  kvActiveDiscussion = id;
  const modalEl = document.getElementById("discussionDetailModal");
  const modal = new bootstrap.Modal(modalEl);
  document.getElementById("ddBody").innerHTML = `<div class="kv-skel" style="height:120px;"></div>`;
  modal.show();
  try {
    const [discussions, comments] = await Promise.all([KevaAPI.discussions(kvDeptId, kvSort), KevaAPI.comments(id)]);
    const d = discussions.find(x => x.id === id);
    document.getElementById("ddTitle").textContent = d?.title || "Discussion";
    document.getElementById("ddBody").innerHTML = `
      <div class="mb-3">
        <div class="d-meta mb-1">${d?.author_name || ""} · ${d ? KevaApp.timeAgo(d.created_at) : ""}</div>
        <p style="font-size:13.8px;">${d?.content || ""}</p>
      </div>
      <hr style="border-color:var(--kv-border);">
      <div id="ddComments">
        ${comments.length ? comments.map(c => `
          <div class="mb-3">
            <div style="font-size:12.8px;font-weight:700;">${c.author_name || "Employee"} <span style="color:var(--kv-text-faint);font-weight:400;">· ${KevaApp.timeAgo(c.created_at)}</span></div>
            <div style="font-size:13.3px;">${c.content}</div>
          </div>`).join("") : `<div class="kv-empty" style="padding:16px;"><i class="fa-regular fa-comment"></i>No replies yet.</div>`}
      </div>
    `;
  } catch (e) { document.getElementById("ddBody").innerHTML = `<div class="text-danger small">${e.message}</div>`; }
}

async function submitComment(e) {
  e.preventDefault();
  const input = document.getElementById("ddCommentInput");
  const content = input.value.trim();
  if (!content || !kvActiveDiscussion) return false;
  try {
    await KevaAPI.addComment(kvActiveDiscussion, content);
    input.value = "";
    openDiscussion(kvActiveDiscussion);
    loadList();
    KevaApp.toast("Reply posted — +2 points");
  } catch (err) { KevaApp.toast(err.message, "error"); }
  return false;
}
