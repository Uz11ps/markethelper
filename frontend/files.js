// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const API_BASE = `${API_BASE_URL}/files`;

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
});

// Добавление аккаунта
document.getElementById("addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const groupIdValue = document.getElementById("group_id").value;
  const payload = {
    group_id: groupIdValue ? parseInt(groupIdValue) : null,
    login: document.getElementById("login").value,
    password: document.getElementById("password").value,
    filename: document.getElementById("filename").value || null,
    skip_auth: document.getElementById("skip_auth").checked || false
  };
  
  try {
    const res = await authFetch(`${API_BASE}/add`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: await res.text() }));
      const errorText = errorData.detail || errorData.message || "Неизвестная ошибка";
      document.getElementById("addResult").innerHTML = `
        <div style="color: red;">
          <strong>Ошибка:</strong> ${errorText}
          ${errorText.includes("skip_auth") ? '<br><br><strong>Совет:</strong> Установите флаг "Пропустить авторизацию" для создания файла без внешнего API' : ''}
        </div>
      `;
      return;
    }
    
    const result = await res.json();
    const skipAuthNote = result.skip_auth ? '<br><small style="color: orange;">⚠ Файл создан без авторизации на внешнем сервисе. Заполните куки вручную.</small>' : '';
    document.getElementById("addResult").innerHTML = `
      <div style="color: green;">
        <strong>Успешно!</strong><br>
        File ID: ${result.file_id}<br>
        Group ID: ${result.group_id}<br>
        Путь: ${result.path}
        ${skipAuthNote}
      </div>
    `;
    
    // Очистка формы
    document.getElementById("addForm").reset();
  } catch (error) {
    document.getElementById("addResult").innerHTML = `<div style="color: red;"><strong>Ошибка:</strong> ${error.message}</div>`;
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
