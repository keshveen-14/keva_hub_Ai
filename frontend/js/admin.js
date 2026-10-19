(async function init() {
  await KevaApp.mount("admin");
  const user = KevaAPI.currentUser();
  if (!user || user.role !== "admin") {
    KevaApp.toast("Admin access required", "error");
    window.location.href = "dashboard.html";
    return;
  }

  const deptOptions = KevaApp.departments.map(d => `<option value="${d.id}">${d.name}</option>`).join("");
  ["aeDept", "genPosterDept", "genPollDept", "genQuizDept"].forEach(id => {
    document.getElementById(id).innerHTML = (id === "aeDept" ? "" : `<option value="">General</option>`) + deptOptions;
  });

  loadEmployees();
  loadDepartments();
})();

function showTab(tab, btn) {
  ["employees", "departments", "content", "announce"].forEach(t => {
    document.getElementById(`tab-${t}`).style.display = t === tab ? "block" : "none";
  });
  document.querySelectorAll("#adminTabs .nav-link").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");
}

async function loadEmployees() {
  const tbody = document.getElementById("empTableBody");
  try {
    const employees = await KevaAPI.employees();
    tbody.innerHTML = employees.map(e => `
      <tr>
        <td class="ps-3">
          <div class="d-flex align-items-center gap-2">
            <div class="kv-avatar" style="width:30px;height:30px;font-size:11px;">${KevaApp.initials(e.name)}</div>
            <div><div style="font-weight:600;">${e.name}</div><div style="font-size:11px;color:var(--kv-text-muted);">${e.email}</div></div>
          </div>
        </td>
        <td><span class="dep-chip ${KevaApp.depClass(e.department_id)}">${KevaApp.depName(e.department_id)}</span></td>
        <td>${e.designation || "—"}</td>
        <td>${e.points || 0}</td>
        <td><span class="badge ${e.status === 'active' ? 'bg-success' : 'bg-secondary'}">${e.status}</span></td>
        <td class="text-end pe-3">
          <button class="btn btn-sm btn-kv-outline me-1" onclick="toggleStatus(${e.id}, '${e.status}')">${e.status === 'active' ? 'Deactivate' : 'Activate'}</button>
          <button class="btn btn-sm" style="color:var(--kv-red);" onclick="removeEmployee(${e.id})"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`).join("");
  } catch (e) { tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted p-4">Couldn't load employees.</td></tr>`; }
}

async function toggleStatus(id, current) {
  try {
    await KevaAPI.updateEmployee(id, { status: current === "active" ? "inactive" : "active" });
    loadEmployees();
  } catch (e) { KevaApp.toast(e.message, "error"); }
}

async function removeEmployee(id) {
  if (!confirm("Remove this employee? This cannot be undone.")) return;
  try { await KevaAPI.deleteEmployee(id); loadEmployees(); KevaApp.toast("Employee removed"); }
  catch (e) { KevaApp.toast(e.message, "error"); }
}

async function addEmployee(e) {
  e.preventDefault();
  try {
    const payload = {
      name: document.getElementById("aeName").value,
      email: document.getElementById("aeEmail").value,
      password: document.getElementById("aePassword").value,
      department_id: parseInt(document.getElementById("aeDept").value),
      designation: document.getElementById("aeDesignation").value,
      role: document.getElementById("aeRole").value,
    };
    await KevaAPI.createEmployee(payload);
    bootstrap.Modal.getInstance(document.getElementById("addEmployeeModal")).hide();
    e.target.reset();
    loadEmployees();
    KevaApp.toast("Employee added");
  } catch (err) { KevaApp.toast(err.message, "error"); }
  return false;
}

async function loadDepartments() {
  const el = document.getElementById("deptList");
  try {
    const deps = await KevaAPI.departments();
    el.innerHTML = deps.map((d, i) => `
      <div class="d-flex align-items-center justify-content-between py-2" style="border-bottom:1px solid var(--kv-border);">
        <div class="d-flex align-items-center gap-2">
          <span class="dep-chip dep-${i % 10}"><i class="fa-solid ${d.icon || 'fa-diagram-project'}"></i></span>
          <div><div style="font-weight:600;font-size:13.5px;">${d.name}</div><div style="font-size:11.5px;color:var(--kv-text-muted);">${d.description || ""}</div></div>
        </div>
        <button class="btn btn-sm" style="color:var(--kv-red);" onclick="removeDepartment(${d.id})"><i class="fa-solid fa-trash"></i></button>
      </div>`).join("");
  } catch (e) { el.innerHTML = `<div class="text-muted">Couldn't load departments.</div>`; }
}

async function addDepartment(e) {
  e.preventDefault();
  try {
    await KevaAPI.createDepartment({
      name: document.getElementById("adName").value,
      description: document.getElementById("adDesc").value,
      icon: document.getElementById("adIcon").value || "fa-diagram-project",
    });
    bootstrap.Modal.getInstance(document.getElementById("addDeptModal")).hide();
    e.target.reset();
    loadDepartments();
    KevaApp.toast("Department added — reload to see it in the sidebar");
  } catch (err) { KevaApp.toast(err.message, "error"); }
  return false;
}

async function removeDepartment(id) {
  if (!confirm("Remove this department? Employees and content stay but lose their department link.")) return;
  try { await KevaAPI.deleteDepartment(id); loadDepartments(); KevaApp.toast("Department removed"); }
  catch (e) { KevaApp.toast(e.message, "error"); }
}

async function genContent(kind) {
  try {
    if (kind === "poster") {
      const dept = document.getElementById("genPosterDept").value;
      const topic = document.getElementById("genPosterTopic").value;
      KevaApp.toast("Generating AI poster...");
      await KevaAPI.generatePoster({ department_id: dept ? parseInt(dept) : null, topic: topic || null });
    } else if (kind === "poll") {
      const dept = document.getElementById("genPollDept").value;
      KevaApp.toast("Generating AI poll...");
      await KevaAPI.generatePoll({ department_id: dept ? parseInt(dept) : null });
    } else if (kind === "quiz") {
      const dept = document.getElementById("genQuizDept").value;
      const num = parseInt(document.getElementById("genQuizNum").value || "5");
      KevaApp.toast("Generating AI quiz...");
      await KevaAPI.generateQuiz({ department_id: dept ? parseInt(dept) : null, num_questions: num });
    }
    KevaApp.toast("Content generated successfully!");
  } catch (e) { KevaApp.toast(e.message, "error"); }
}

async function sendAnnouncement() {
  const title = document.getElementById("annTitle").value.trim();
  const message = document.getElementById("annMessage").value.trim();
  if (!title || !message) { KevaApp.toast("Title and message are required", "error"); return; }
  try {
    await KevaAPI.request(`/notifications/announce`, { method: "POST", params: { title, message } });
    document.getElementById("annTitle").value = "";
    document.getElementById("annMessage").value = "";
    KevaApp.toast("Announcement sent to all employees");
  } catch (e) { KevaApp.toast(e.message, "error"); }
}
