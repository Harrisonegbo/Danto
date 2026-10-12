let token = localStorage.getItem("token");
let ws = null;

function showMsg(text, isError = false) {
  const el = document.getElementById("auth-msg");
  el.textContent = text;
  el.className = "msg " + (isError ? "error" : "ok");
}

async function login() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  if (!username || !password) {
    showMsg("Please enter username and password", true);
    return;
  }

  const form = new FormData();
  form.append("username", username);
  form.append("password", password);

  try {
    const res = await fetch("/token", { method: "POST", body: form });
    const data = await res.json();
    if (data.access_token) {
      token = data.access_token;
      localStorage.setItem("token", token);
      showMsg("Login successful");
      showApp(username);
    } else {
      showMsg(data.detail || "Login failed", true);
    }
  } catch (e) {
    showMsg("Network error", true);
  }
}

async function register() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  if (!username || !password) {
    showMsg("Please enter username and password", true);
    return;
  }
  try {
    const res = await fetch(`/register?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`, {
      method: "POST"
    });
    const data = await res.json();
    if (res.ok) {
      showMsg("Registered successfully – you can now login");
    } else {
      showMsg(data.detail || "Registration failed", true);
    }
  } catch (e) {
    showMsg("Network error", true);
  }
}

function logout() {
  localStorage.removeItem("token");
  token = null;
  if (ws) ws.close();
  location.reload();
}

function showApp(username) {
  document.getElementById("auth-section").style.display = "none";
  document.getElementById("app-section").style.display = "block";
  document.getElementById("user-display").textContent = username || "User";
  connectWS();
  loadBacktests();
}

function connectWS() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${protocol}//${location.host}/ws/signals`);

  ws.onopen = () => {
    const box = document.getElementById("signals");
    box.innerHTML = `<p class="muted">Connected to paper-signal stream</p>`;
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      const box = document.getElementById("signals");
      const time = new Date().toLocaleTimeString();
      let html = "";
      if (msg.type === "signal") {
        const side = msg.signal === 1 ? "LONG" : msg.signal === -1 ? "SHORT" : "FLAT";
        html = `<p><strong>${time}</strong> → ${side} | Conf: ${(msg.confidence * 100).toFixed(1)}% | Price: ${msg.price}</p>`;
      } else {
        html = `<p class="muted">${time} – ${msg.msg || JSON.stringify(msg)}</p>`;
      }
      box.innerHTML = html + box.innerHTML;
    } catch (e) {}
  };

  ws.onclose = () => {
    const box = document.getElementById("signals");
    box.innerHTML = `<p class="muted">Disconnected. Reconnecting in 3s...</p>` + box.innerHTML;
    setTimeout(connectWS, 3000);
  };
}

function sendPing() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send("ping");
  }
}

async function loadBacktests() {
  if (!token) return;
  try {
    const res = await fetch("/api/backtests", {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed");
    const data = await res.json();
    const box = document.getElementById("backtests");
    if (!data.length) {
      box.innerHTML = `<p class="muted">No saved backtests yet.</p>`;
      return;
    }
    box.innerHTML = data.map(b => {
      const eq = b.stats.final_equity ? b.stats.final_equity.toFixed(3) : "n/a";
      const wr = b.stats.win_rate != null ? (b.stats.win_rate * 100).toFixed(1) + "%" : "n/a";
      return `<div>#${b.id} – ${b.created_at.slice(0,19)} – Equity ${eq}× – WR ${wr}</div>`;
    }).join("");
  } catch (e) {
    document.getElementById("backtests").innerHTML = `<p class="muted">Could not load backtests</p>`;
  }
}

// Auto-login if token exists
if (token) {
  // We don't have the username stored, just show the app
  showApp("User");
}
