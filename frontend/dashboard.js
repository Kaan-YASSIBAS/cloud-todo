/* ======================================
   CONFIG
====================================== */
const { AUTH_URL, TASK_URL } = window.APP_CONFIG;

/* ======================================
   GLOBAL STATE
====================================== */
let currentWeekStart = getMonday(new Date());
let selectedDay = new Date(currentWeekStart);
const today = new Date();
if (today >= currentWeekStart && today < new Date(currentWeekStart.getTime() + 7*86400000)) {
  selectedDay = today;
}

let editingTaskId = null;
let lastTasks = [];

/* ======================================
   AUTH CHECK & LOGOUT
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

    if (!res.ok) throw new Error("Auth failed");

    const user = await res.json();
    document.getElementById("profileName").textContent = user.username;
    document.getElementById("profileEmail").textContent = user.email || "user@example.com";
  } catch {
    logout();
  }
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "index.html";
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

  const endOfWeek = new Date(currentWeekStart.getTime() + 6 * 86400000);
  
  const options = { month: 'short', day: 'numeric' };
  weekRangeEl.textContent = 
    currentWeekStart.toLocaleDateString('en-US', options) + " - " + 
    endOfWeek.toLocaleDateString('en-US', options);

  daySelector.innerHTML = "";

  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart.getTime() + i * 86400000);
    const div = document.createElement("div");
    
    div.textContent = date.toLocaleDateString('en-US', { weekday: 'short' });

    if (date.toDateString() === selectedDay.toDateString()) {
      div.classList.add("active");
    }

    div.onclick = () => {
      selectedDay = date;
      loadWeek();
      renderTasksGrid();
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

  try {
    const res = await fetch(`${TASK_URL}/tasks`, {
      headers: { "Authorization": "Bearer " + token }
    });

    if (res.status === 401) {
      logout();
      return;
    }

    const data = await res.json();
    lastTasks = data.items || [];
    
    renderWeeklySummary(lastTasks);
    renderTasksGrid();
  } catch (err) {
    console.error("Failed to load tasks", err);
  }
}

/* ======================================
   RENDER: WEEKLY SUMMARY (Sidebar)
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
    const total = dayTasks.length;

    const li = document.createElement("li");
    li.innerHTML = `
      <span>${date.toLocaleDateString('en-US', { weekday: 'short' })}</span>
      <span style="opacity:0.6">${done}/${total} done</span>
    `;
    list.appendChild(li);
  }
}

/* ======================================
   RENDER: TASK GRID (Kart Görünümü)
====================================== */
function renderTasksGrid() {
  const grid = document.getElementById("taskGrid");
  grid.innerHTML = "";

  const daysTasks = lastTasks.filter(task => {
    if (!task.due_date) return false;
    const date = new Date(task.due_date);
    return date.toDateString() === selectedDay.toDateString();
  });

  daysTasks.sort((a, b) => new Date(a.due_date) - new Date(b.due_date));

  if (daysTasks.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: #999; margin-top: 40px;">
        <p>No tasks for this day. Enjoy your free time!</p>
      </div>
    `;
    // updateProgress çağrısı kaldırıldı çünkü widget silindi
    return;
  }

  daysTasks.forEach((task, index) => {
    const date = new Date(task.due_date);
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const card = document.createElement("div");
    // YENİ PALETE GÖRE 7 RENK DÖNGÜSÜ
    const colorClass = `pastel-${(index % 7) + 1}`;
    
    card.className = `task-card ${colorClass}`;
    if(task.status === 'done') {
      card.style.opacity = "0.6";
      card.style.transform = "scale(0.98)";
    }

    card.innerHTML = `
      <div class="task-header">
        <span class="task-time-badge">${timeStr}</span>
        ${task.status === 'done' ? '<span>✅</span>' : ''}
      </div>
      
      <div class="task-title">${task.title}</div>
      <div class="task-desc">${task.description || "No description"}</div>

      <div class="card-footer">
        <button class="icon-btn btn-done" onclick="markDone(${task.id})" title="Complete">
          ✔
        </button>
        <button class="icon-btn btn-edit" onclick="openEdit(${task.id})" title="Edit">
          ✎
        </button>
        <button class="icon-btn btn-del" onclick="deleteTask(${task.id})" title="Delete">
          🗑
        </button>
      </div>
    `;

    grid.appendChild(card);
  });

  // updateProgress çağrısı kaldırıldı
}

/* ======================================
   CREATE TASK
====================================== */
async function createNewTask() {
  const title = document.getElementById("taskTitle").value;
  const desc = document.getElementById("taskDesc").value;
  let date = document.getElementById("taskDate").value;
  let time = document.getElementById("taskTime").value;

  if (!title) {
    alert("Please enter a task title");
    return;
  }

  if (!date) {
    const year = selectedDay.getFullYear();
    const month = String(selectedDay.getMonth() + 1).padStart(2, '0');
    const day = String(selectedDay.getDate()).padStart(2, '0');
    date = `${year}-${month}-${day}`;
  }
  
  if (!time) time = "09:00";

  const fullDate = `${date}T${time}:00`;
  const token = localStorage.getItem("token");

  try {
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
    
    document.getElementById("taskTitle").value = "";
    document.getElementById("taskDesc").value = "";
    
    loadTasks();
  } catch (err) {
    alert("Error creating task");
  }
}

/* ======================================
   EDIT / DELETE / MARK DONE
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
    const hours = String(d.getHours()).padStart(2,'0');
    const minutes = String(d.getMinutes()).padStart(2,'0');
    document.getElementById("editTime").value = `${hours}:${minutes}`;
  }

  document.getElementById("editModal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("editModal").classList.add("hidden");
}

async function saveEdit() {
  const token = localStorage.getItem("token");
  const title = document.getElementById("editTitle").value;
  const desc = document.getElementById("editDesc").value;
  const date = document.getElementById("editDate").value;
  const time = document.getElementById("editTime").value;

  let body = { title, description: desc };

  if (date && time) {
    body.due_date = `${date}T${time}:00`;
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

async function deleteTask(id) {
  if (!confirm("Are you sure you want to delete this task?")) return;
  const token = localStorage.getItem("token");
  await fetch(`${TASK_URL}/tasks/${id}`, {
    method: "DELETE",
    headers: { "Authorization": "Bearer " + token }
  });
  loadTasks();
}

/* ======================================
   INIT
====================================== */
window.onload = () => {
  checkAuth();
  loadWeek();
};