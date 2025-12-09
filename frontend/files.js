// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const API_BASE = `${API_BASE_URL}/files`;

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
});

// Добавление аккаунта
document.getElementById("addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    group_id: parseInt(document.getElementById("group_id").value) || null,
    login: document.getElementById("login").value,
    password: document.getElementById("password").value,
    filename: document.getElementById("filename").value || null
  };
  
  try {
    const res = await authFetch(`${API_BASE}/add`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      const errorText = await res.text();
      document.getElementById("addResult").textContent = `Ошибка: ${errorText}`;
      document.getElementById("addResult").style.color = "red";
      return;
    }
    
    const result = await res.json();
    document.getElementById("addResult").textContent = `Успешно! File ID: ${result.file_id}, Group ID: ${result.group_id}`;
    document.getElementById("addResult").style.color = "green";
    
    // Очистка формы
    document.getElementById("addForm").reset();
  } catch (error) {
    document.getElementById("addResult").textContent = `Ошибка: ${error.message}`;
    document.getElementById("addResult").style.color = "red";
  }
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
