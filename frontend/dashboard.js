/* ======================================
   CONFIG
====================================== */
const { AUTH_URL, TASK_URL } = window.APP_CONFIG;

/* ======================================
   GLOBAL STATE
====================================== */
let currentWeekStart = getMonday(new Date());
let selectedDay = new Date(currentWeekStart);
let editingTaskId = null;
let draggedTaskId = null;
let lastTasks = [];   // son çekilen task listesi

/* ======================================
   AUTH CHECK
====================================== */
async function checkAuth() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  try {
    const res = await fetch(`${AUTH_URL}/me`, {
      headers: { "Authorization": "Bearer " + token }
    });

    if (!res.ok) {
      localStorage.removeItem("token");
      window.location.href = "index.html";
      return;
    }

    const user = await res.json();
    document.getElementById("profileName").textContent = user.username;
    document.getElementById("profileEmail").textContent = user.email || "";
  } catch {
    localStorage.removeItem("token");
    window.location.href = "index.html";
  }
}

/* ======================================
   WEEK CALCULATION
====================================== */
function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - (day === 0 ? 6 : day - 1);
  return new Date(d.setDate(diff));
}

function prevWeek() {
  currentWeekStart.setDate(currentWeekStart.getDate() - 7);
  loadWeek();
}

function nextWeek() {
  currentWeekStart.setDate(currentWeekStart.getDate() + 7);
  loadWeek();
}

/* ======================================
   LOAD WEEK UI
====================================== */
function loadWeek() {
  const weekRangeEl = document.getElementById("weekRange");
  const daySelector = document.getElementById("daySelector");

  weekRangeEl.textContent =
    currentWeekStart.toDateString() + " - " +
    new Date(currentWeekStart.getTime() + 6 * 86400000).toDateString();

  daySelector.innerHTML = "";

  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart.getTime() + i * 86400000);
    const div = document.createElement("div");
    div.textContent = date.toDateString().slice(0, 3);

    if (date.toDateString() === selectedDay.toDateString()) {
      div.classList.add("active");
    }

    div.onclick = () => {
      selectedDay = date;
      loadWeek();
      loadTasks();
    };

    daySelector.appendChild(div);
  }

  loadTasks();
}

/* ======================================
   LOAD TASKS
====================================== */
async function loadTasks() {
  const token = localStorage.getItem("token");

  const res = await fetch(`${TASK_URL}/tasks`, {
    headers: { "Authorization": "Bearer " + token }
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "index.html";
    return;
  }

  const data = await res.json();
  const tasks = data.items;
  lastTasks = tasks;   // global olarak sakla

  renderWeeklySummary(tasks);
  renderTimeline(tasks);
}

/* ======================================
   LEFT SIDEBAR — WEEKLY SUMMARY
====================================== */
function renderWeeklySummary(tasks) {
  const list = document.getElementById("weeklyList");
  list.innerHTML = "";

  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart.getTime() + i * 86400000);

    const dayTasks = tasks.filter(t => {
      if (!t.due_date) return false;
      const d = new Date(t.due_date);
      return d.toDateString() === date.toDateString();
    });

    const done = dayTasks.filter(t => t.status === "done").length;

    const li = document.createElement("li");
    li.textContent = `${date.toDateString().slice(0,3)} – ${dayTasks.length} tasks (${done} done)`;
    list.appendChild(li);
  }
}

/* ======================================
   TIMELINE RENDER
====================================== */
function renderTimeline(tasks) {
  const timeline = document.getElementById("timeline");
  timeline.innerHTML = "";

  for (let hour = 0; hour < 24; hour++) {
    const hourDiv = document.createElement("div");
    hourDiv.className = "timeline-hour";
    hourDiv.dataset.time = hour.toString().padStart(2, '0') + ":00";

    hourDiv.setAttribute("ondragover", "allowDrop(event)");
    hourDiv.setAttribute("ondrop", `dropTask(event, ${hour})`);

    timeline.appendChild(hourDiv);
  }

  tasks.forEach(task => {
    if (!task.due_date) return;

    const date = new Date(task.due_date);
    if (date.toDateString() !== selectedDay.toDateString()) return;

    const hour = date.getHours();
    const hourBlock = timeline.querySelector(`.timeline-hour:nth-child(${hour + 1})`);

    const card = document.createElement("div");
    card.className = "task-card";
    card.draggable = true;

    card.setAttribute("ondragstart", `dragStart(event, ${task.id})`);

    card.innerHTML = `
      <div class="task-time">${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
      <div class="task-title">${task.title}</div>
      <div class="task-desc">${task.description || ""}</div>

      <div class="task-actions">
        <button class="btn-complete" onclick="markDone(${task.id})">✓</button>
        <button class="btn-edit" onclick="openEdit(${task.id})">✎</button>
        <button class="btn-delete" onclick="deleteTask(${task.id})">🗑</button>
      </div>
    `;

    hourBlock.appendChild(card);
  });

  updateProgress(tasks);
}

/* ======================================
   PROGRESS RING
====================================== */
function updateProgress(tasks) {
  const done = tasks.filter(t => t.status === "done").length;
  const total = tasks.length;
  const percent = total === 0 ? 0 : Math.round(done / total * 100);

  document.getElementById("progressValue").textContent = percent + "%";
}

/* ======================================
   CREATE TASK
====================================== */
async function createNewTask() {
  const title = document.getElementById("taskTitle").value;
  const desc = document.getElementById("taskDesc").value;
  const date = document.getElementById("taskDate").value;
  const time = document.getElementById("taskTime").value;

  if (!title || !date || !time) {
    alert("Please fill all required fields");
    return;
  }

  const fullDate = `${date}T${time}:00`;
  const token = localStorage.getItem("token");

  await fetch(`${TASK_URL}/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify({
      title,
      description: desc,
      due_date: fullDate
    })
  });

  loadTasks();
}

/* ======================================
   EDIT — OPEN MODAL
====================================== */
function openEdit(id) {
  editingTaskId = id;

  const task = lastTasks.find(t => t.id === id);
  if (!task) return;

  document.getElementById("editTitle").value = task.title;
  document.getElementById("editDesc").value = task.description || "";

  if (task.due_date) {
    const d = new Date(task.due_date);
    document.getElementById("editDate").value = d.toISOString().slice(0, 10);
    document.getElementById("editTime").value = d.toTimeString().slice(0, 5);
  }

  document.getElementById("editModal").classList.remove("hidden");
}

/* CLOSE MODAL */
function closeModal() {
  document.getElementById("editModal").classList.add("hidden");
}

/* SAVE EDIT */
async function saveEdit() {
  const token = localStorage.getItem("token");

  const title = document.getElementById("editTitle").value;
  const desc = document.getElementById("editDesc").value;
  const date = document.getElementById("editDate").value;
  const time = document.getElementById("editTime").value;

  let body = { title, description: desc };

  if (date && time) {
    const fullDate = `${date}T${time}:00`;
    body.due_date = fullDate;
  }

  await fetch(`${TASK_URL}/tasks/${editingTaskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify(body)
  });

  closeModal();
  loadTasks();
}

/* ======================================
   MARK DONE
====================================== */
async function markDone(id) {
  const token = localStorage.getItem("token");

  await fetch(`${TASK_URL}/tasks/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify({ status: "done" })
  });

  loadTasks();
}

/* ======================================
   DELETE TASK
====================================== */
async function deleteTask(id) {
  if (!confirm("Delete this task?")) return;

  const token = localStorage.getItem("token");

  await fetch(`${TASK_URL}/tasks/${id}`, {
    method: "DELETE",
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  loadTasks();
}

/* ======================================
   DRAG & DROP
====================================== */
function dragStart(ev, id) {
  draggedTaskId = id;
}

function allowDrop(ev) {
  ev.preventDefault();
}

async function dropTask(ev, hour) {
  ev.preventDefault();

  const token = localStorage.getItem("token");

  const newDate = new Date(selectedDay);
  newDate.setHours(hour);
  newDate.setMinutes(0);

  // YYYY-MM-DDTHH:MM:00 formatında local datetime
  const yyyy = newDate.getFullYear();
  const mm = String(newDate.getMonth() + 1).padStart(2, "0");
  const dd = String(newDate.getDate()).padStart(2, "0");
  const hh = String(newDate.getHours()).padStart(2, "0");
  const mi = String(newDate.getMinutes()).padStart(2, "0");
  const fullDate = `${yyyy}-${mm}-${dd}T${hh}:${mi}:00`;

  await fetch(`${TASK_URL}/tasks/${draggedTaskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify({
      due_date: fullDate
    })
  });

  loadTasks();
}

/* ======================================
   INIT
====================================== */
window.onload = () => {
  checkAuth();
  loadWeek();
  loadTasks();
};
