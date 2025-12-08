// Конфигурация API
const API_BASE_URL = window.location.origin + '/api';
const API_BASE = `${API_BASE_URL}/files`;

// Добавление аккаунта
document.getElementById("addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    group_id: parseInt(document.getElementById("group_id").value),
    login: document.getElementById("login").value,
    password: document.getElementById("password").value,
    filename: document.getElementById("filename").value || null
  };
  const res = await fetch(`${API_BASE}/add`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  document.getElementById("addResult").textContent = await res.text();
});

// Получение файла
document.getElementById("getForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const tgId = document.getElementById("tg_id").value;
  const res = await fetch(`${API_BASE}/user/${tgId}/get`);
  document.getElementById("getResult").textContent = await res.text();
});

// Перегенерация куков
document.getElementById("regenForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const tgId = document.getElementById("regen_tg_id").value;
  const filename = document.getElementById("regen_filename").value;
  const res = await fetch(`${API_BASE}/user/${tgId}/regen`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(filename ? { filename } : {})
  });
  document.getElementById("regenResult").textContent = await res.text();
});
