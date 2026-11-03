const TOKEN_KEY = "admin_chatbot_token";
const $ = (id) => document.getElementById(id);

const loginView = $("login-view");
const appView = $("app-view");
const messagesEl = $("messages");

let currentRole = "user";

function getToken() { try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; } }
function setToken(t) { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch (e) {} }

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(path, { ...options, headers });
  let data = {};
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) {
    const err = new Error(data.detail || "Something went wrong.");
    err.status = res.status;
    throw err;
  }
  return data;
}

/* ---------- views ---------- */
function showLogin() {
  setToken(null);
  currentRole = "user";
  appView.classList.add("hidden");
  $("users-panel").classList.add("hidden");
//   $("chips").classList.add("hidden");
  loginView.classList.remove("hidden");
  $("email").focus();
}

// me = { email, name, role }
function showApp(me) {
  currentRole = me.role;
  const isAdmin = currentRole === "admin";

  loginView.classList.add("hidden");
  appView.classList.remove("hidden");

  $("who-email").textContent = me.email;
  const badge = $("who-role");
  badge.textContent = isAdmin ? "Admin" : "User";
  badge.className = "role-badge" + (isAdmin ? "" : " user");

  // Only the admin sees the users panel and the CRUD shortcuts
  $("users-panel").classList.toggle("hidden", !isAdmin);
//   $("chips").classList.toggle("hidden", !isAdmin);
  $("chat-input").placeholder = isAdmin
    ? "Type a command, e.g. add the user ..."
    : "Type your message...";

  messagesEl.innerHTML = "";
  if (isAdmin) {
    addMessage("bot",
      "Hi! I can add, update and remove users for you. Just tell me what to do in plain English, for example:\n" +
      "\u2022 Add the user \"john.smith@xyz.com\" with phone number \"+92332\"\n" +
      "\u2022 Update samantha's city to Cordoba\n" +
      "\u2022 Remove the user \"john.smith@xyz.com\"");
    refreshUsers();
  } else {
    addMessage("bot", "Hi" + (me.name ? " " + me.name : "") + "! \uD83D\uDC4B How can I help you today?");
  }
  $("chat-input").focus();
}

/* ---------- login (by registered email) ---------- */
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("login-btn");
  $("login-error").textContent = "";
  btn.disabled = true;
  try {
    const data = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({ email: $("email").value.trim() }),
    });
    setToken(data.token);
    showApp(data);   // data has email, name, role
  } catch (err) {
    $("login-error").textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("logout-btn").addEventListener("click", async () => {
  try { await api("/api/logout", { method: "POST" }); } catch (e) {}
  showLogin();
});

/* ---------- chat ---------- */
function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function addTyping() {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("chat-input");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
//   $("chips").classList.add("hidden");
  addMessage("user", text);
  const typing = addTyping();
  $("send-btn").disabled = true;

  try {
    const data = await api("/api/chat", { method: "POST", body: JSON.stringify({ message: text }) });
    typing.remove();
    addMessage("bot", data.reply);
    refreshUsers();   // does nothing for normal users
  } catch (err) {
    typing.remove();
    if (err.status === 401) { showLogin(); return; }
    addMessage("bot", "Error: " + err.message);
  } finally {
    $("send-btn").disabled = false;
    input.focus();
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    $("chat-input").value = chip.dataset.text;
    $("chat-input").focus();
  });
});

/* ---------- users list (admin only) ---------- */
async function refreshUsers() {
  if (currentRole !== "admin") return;
  try {
    const data = await api("/api/users");
    const list = $("user-list");
    list.innerHTML = "";
    $("user-count").textContent = data.users.length + " total";
    if (!data.users.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "No users yet.";
      list.appendChild(empty);
      return;
    }
    data.users.forEach((u) => {
      const row = document.createElement("div");
      row.className = "user";
      const n = document.createElement("div"); n.className = "n"; n.textContent = u.name || "(no name)";
      const e = document.createElement("div"); e.className = "e"; e.textContent = u.email;
      const m = document.createElement("div"); m.className = "meta";
      m.textContent = [u.phone, u.city].filter(Boolean).join(" \u00b7 ") || "No phone or city";
      row.append(n, e, m);
      list.appendChild(row);
    });
  } catch (err) {
    if (err.status === 401) showLogin();
  }
}

/* ---------- start: auto login if a saved session is still valid ---------- */
(async function init() {
  if (getToken()) {
    try {
      const me = await api("/api/me");
      showApp(me);   // me has email, name, role
      return;
    } catch (e) {}
  }
  showLogin();
})();