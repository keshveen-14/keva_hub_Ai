let kvDeptId = null;
let kvQuiz = null;

(async function init() {
  await KevaApp.mount("quiz");
  const params = new URLSearchParams(window.location.search);
  kvDeptId = params.get("department_id") ? parseInt(params.get("department_id")) : null;
  document.getElementById("kvDeptEyebrow").textContent = kvDeptId ? KevaApp.depName(kvDeptId) : "AI Quiz · All Departments";

  const user = KevaAPI.currentUser();
  if (user?.role === "admin") document.getElementById("kvGenQuizBtn").style.display = "inline-block";

  loadQuiz();
})();

async function loadQuiz() {
  const el = document.getElementById("kvQuizArea");
  el.innerHTML = `<div class="kv-skel" style="height:300px;"></div>`;
  try {
    kvQuiz = await KevaAPI.todayQuiz(kvDeptId);
    if (!kvQuiz) { el.innerHTML = `<div class="kv-empty"><i class="fa-solid fa-circle-question"></i>No quiz available yet for this department.</div>`; return; }
    renderQuiz();
  } catch (e) { el.innerHTML = `<div class="kv-empty"><i class="fa-solid fa-triangle-exclamation"></i>Couldn't load the quiz.</div>`; }
}

function renderQuiz() {
  const el = document.getElementById("kvQuizArea");
  el.innerHTML = `
    <div class="kv-eyebrow signal mb-2"><i class="fa-solid fa-sparkles"></i>${kvQuiz.title}</div>
    <form id="quizForm" onsubmit="return submitQuizForm(event)">
      ${kvQuiz.questions.map((q, i) => `
        <div class="mb-4">
          <div style="font-weight:700;font-size:14px;margin-bottom:10px;">${i + 1}. ${q.question}</div>
          ${["a", "b", "c", "d"].map(letter => `
            <label class="d-flex align-items-center gap-2 mb-2" style="cursor:pointer;font-size:13.5px;">
              <input type="radio" name="q_${q.id}" value="${letter.toUpperCase()}" required>
              <span>${q["option_" + letter]}</span>
            </label>`).join("")}
        </div>`).join("")}
      <button type="submit" class="btn btn-kv-primary">Submit Quiz</button>
    </form>
    <div id="quizResult" class="mt-3"></div>
  `;
}

async function submitQuizForm(e) {
  e.preventDefault();
  const answers = {};
  kvQuiz.questions.forEach(q => {
    const picked = document.querySelector(`input[name="q_${q.id}"]:checked`);
    if (picked) answers[q.id] = picked.value;
  });
  try {
    const res = await KevaAPI.submitQuiz(kvQuiz.id, answers);
    document.getElementById("quizResult").innerHTML = `
      <div class="alert" style="background:var(--kv-signal-light);color:var(--kv-signal);border:none;border-radius:12px;font-weight:700;">
        You scored ${res.score}/${res.total} — earned +${res.points_earned} points! 🎉
      </div>`;
    document.querySelectorAll("#quizForm input").forEach(i => i.disabled = true);
    KevaApp.toast(`Quiz complete: ${res.score}/${res.total}`);
  } catch (err) { KevaApp.toast(err.message, "error"); }
  return false;
}

async function genQuiz() {
  try {
    KevaApp.toast("Generating AI quiz...");
    await KevaAPI.generateQuiz({ department_id: kvDeptId });
    loadQuiz();
    KevaApp.toast("New quiz generated!");
  } catch (e) { KevaApp.toast(e.message, "error"); }
}
