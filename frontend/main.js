const { AUTH_URL, TASK_URL } = window.APP_CONFIG;

function getToken() {
  return localStorage.getItem("token");
}

async function handleLogin() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const errorEl = document.getElementById("error");

  if (!username || !password) {
    errorEl.textContent = "Please fill all fields";
    return;
  }

  try {
    const res = await fetch(`${AUTH_URL}/login`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      errorEl.textContent = "Invalid credentials";
      return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);

    window.location.href = "dashboard.html";
  } catch (err) {
    errorEl.textContent = "Server error";
  }
}
