const { AUTH_URL, TASK_URL } = window.APP_CONFIG;

function getToken() {
  return localStorage.getItem("token");
}

/* ======================================
   EKRAN DEĞİŞTİRME (TOGGLE)
====================================== */
function toggleForms(target) {
  const loginBox = document.getElementById("login-box");
  const registerBox = document.getElementById("register-box");
  const subtitle = document.getElementById("page-subtitle");
  
  // Mesajları temizle
  document.getElementById("error").textContent = "";
  document.getElementById("success").textContent = "";

  if (target === 'register') {
    loginBox.classList.add("hidden");
    registerBox.classList.remove("hidden");
    subtitle.textContent = "Create an account to start";
  } else {
    registerBox.classList.add("hidden");
    loginBox.classList.remove("hidden");
    subtitle.textContent = "Please login to continue";
  }
}

/* ======================================
   GİRİŞ YAP (LOGIN)
====================================== */
async function handleLogin() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const errorEl = document.getElementById("error");
  const successEl = document.getElementById("success");

  // Önce mesajları temizle
  errorEl.textContent = "";
  successEl.textContent = "";

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

/* ======================================
   KAYIT OL (REGISTER) - YENİ
====================================== */
async function handleRegister() {
  const username = document.getElementById("reg-username").value.trim();
  const password = document.getElementById("reg-password").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  
  const errorEl = document.getElementById("error");
  const successEl = document.getElementById("success");

  errorEl.textContent = "";
  successEl.textContent = "";

  if (!username || !password) {
    errorEl.textContent = "Username and password are required";
    return;
  }

  try {
    // Backend'in beklediği JSON formatı
    const res = await fetch(`${AUTH_URL}/register`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ 
        username, 
        password,
        email: email || null 
      })
    });

    // Kullanıcı adı zaten varsa (Backend 409 dönüyor)
    if (res.status === 409) {
      errorEl.textContent = "Username already exists!";
      return;
    }

    if (!res.ok) {
      errorEl.textContent = "Registration failed";
      return;
    }

    // Başarılı ise
    successEl.textContent = "Account created! Redirecting to login...";
    
    // 1.5 saniye sonra giriş ekranına at
    setTimeout(() => {
      toggleForms('login');
      // Kullanıcının adını otomatik dolduralım
      document.getElementById("username").value = username;
      successEl.textContent = "Account created. Please login.";
    }, 1500);

  } catch (err) {
    errorEl.textContent = "Server error during registration";
  }
}