// Конфигурация API (используется из auth.js)
// const API_BASE_URL уже объявлен в auth.js

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadRequests();
});

async function loadRequests() {
  try {
    console.log(`[loadRequests] Загрузка заявок из: ${API_BASE_URL}/admin/requests/`);
    const res = await authFetch(`${API_BASE_URL}/admin/requests/`);
    console.log(`[loadRequests] Ответ API:`, res.status, res.statusText);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`[loadRequests] Ошибка API:`, errorText);
      throw new Error(`Ошибка запроса: ${res.status} - ${errorText}`);
    }

    const data = await res.json();
    console.log(`[loadRequests] Получено заявок:`, data.length);
    console.log(`[loadRequests] Данные:`, data);

    const tbody = document.querySelector("#requestsTable tbody");
    tbody.innerHTML = "";

    // Фильтруем только новые заявки
    const pending = data.filter(req => {
      console.log(`[loadRequests] Проверка заявки:`, req.id, `status="${req.status}"`);
      return req.status === "В ожидании";
    });
    
    console.log(`[loadRequests] Отфильтровано заявок со статусом "В ожидании":`, pending.length);

    if (pending.length === 0) {
      console.log(`[loadRequests] Нет заявок со статусом "В ожидании"`);
      // Показываем все заявки для отладки
      if (data.length > 0) {
        tbody.innerHTML = `<tr><td colspan="7">Нет заявок со статусом "В ожидании". Всего заявок: ${data.length}. Статусы: ${data.map(r => r.status).join(', ')}</td></tr>`;
      } else {
        tbody.innerHTML = `<tr><td colspan="7">Новых заявок нет</td></tr>`;
      }
      return;
    }

    pending.forEach(req => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${req.id}</td>
        <td>
          ${req.username 
            ? `<a href="https://t.me/${req.username}" target="_blank">@${req.username}</a>` 
            : `<span style="color: gray;">нет username</span>`}
        </td>
        <td>${req.tariff_code}</td>
        <td>${req.duration_months} мес.</td>
        <td>${req.status}</td>
        <td>${new Date(req.created_at).toLocaleDateString()}</td>
        <td>
          <input type="text" id="filename-${req.id}" placeholder="Имя файла" />
          <button class="approve" onclick="approve(${req.id})">Принять</button>
          <button class="reject" onclick="reject(${req.id})">Отклонить</button>
        </td>
      `;

      tbody.appendChild(row);
    });


  } catch (err) {
    console.error("Ошибка при загрузке заявок:", err);
    const tbody = document.querySelector("#requestsTable tbody");
    tbody.innerHTML = `<tr><td colspan="7">Ошибка при загрузке заявок</td></tr>`;
  }
}
async function approve(id) {
  try {
    const input = document.querySelector(`#filename-${id}`);
    const filename = input.value.trim();

    const res = await authFetch(`${API_BASE_URL}/admin/requests/${id}/approve`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ filename: filename || null })
    });

    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    loadRequests();
  } catch (err) {
    console.error(err);
    alert("Не удалось принять заявку: " + err.message);
  }
}

async function reject(id) {
  try {
    const res = await authFetch(`${API_BASE_URL}/admin/requests/${id}/reject`, {
      method: "POST"
    });
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    loadRequests();
  } catch (err) {
    console.error(err);
    alert("Не удалось отклонить заявку: " + err.message);
  }
}

loadRequests();
