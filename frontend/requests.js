// Конфигурация API (используется из auth.js)
// const API_BASE_URL уже объявлен в auth.js

let groupsList = [];

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadGroups();
  loadRequests();
});

// Загрузка списка групп
async function loadGroups() {
  try {
    const res = await authFetch(`${API_BASE_URL}/admin/groups/`);
    if (res.ok) {
      groupsList = await res.json();
    }
  } catch (err) {
    console.error("Ошибка при загрузке групп:", err);
  }
}

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
      return req.status === "Pending" || req.status === "В ожидании";
    });
    
    console.log(`[loadRequests] Отфильтровано заявок со статусом "Pending":`, pending.length);

    if (pending.length === 0) {
      console.log(`[loadRequests] Нет заявок со статусом "Pending"`);
      if (data.length > 0) {
        tbody.innerHTML = `<tr><td colspan="8">Нет заявок со статусом "Pending". Всего заявок: ${data.length}. Статусы: ${data.map(r => r.status).join(', ')}</td></tr>`;
      } else {
        tbody.innerHTML = `<tr><td colspan="8">Новых заявок нет</td></tr>`;
      }
      return;
    }

    pending.forEach(req => {
      const row = document.createElement("tr");
      const subscriptionType = req.subscription_type || "group";
      const typeLabel = subscriptionType === "individual" ? "👤 Индивидуальный" : "📦 Складчина";
      
      // Для складчины показываем выбор группы, для индивидуального - не показываем
      let groupSelect = '';
      if (subscriptionType === "group") {
        groupSelect = `
          <select id="group-${req.id}" style="margin-bottom: 5px; width: 100%;">
            <option value="">Выберите группу</option>
            ${groupsList.map(g => `<option value="${g.id}" ${g.id === req.group_id ? 'selected' : ''}>${g.name}</option>`).join('')}
          </select>
        `;
      } else {
        groupSelect = `<span style="color: gray;">Индивидуальный доступ</span>`;
      }

      row.innerHTML = `
        <td>${req.id}</td>
        <td>
          ${req.username 
            ? `<a href="https://t.me/${req.username}" target="_blank">@${req.username}</a>` 
            : `<span style="color: gray;">нет username</span>`}
        </td>
        <td>${req.tariff_code}</td>
        <td>${req.duration_months} мес.</td>
        <td>${typeLabel}</td>
        <td>${req.status}</td>
        <td>${new Date(req.created_at).toLocaleDateString()}</td>
        <td>
          ${groupSelect}
          ${subscriptionType === "individual" && req.user_email ? `<div style="font-size: 0.9em; color: #666;">Email: ${req.user_email}</div>` : ''}
          <button class="approve" onclick="approve(${req.id}, '${subscriptionType}')">Принять</button>
          <button class="reject" onclick="reject(${req.id})">Отклонить</button>
        </td>
      `;

      tbody.appendChild(row);
    });


  } catch (err) {
    console.error("Ошибка при загрузке заявок:", err);
    const tbody = document.querySelector("#requestsTable tbody");
    tbody.innerHTML = `<tr><td colspan="8">Ошибка при загрузке заявок</td></tr>`;
  }
}

async function approve(id, subscriptionType) {
  try {
    let groupId = null;
    
    if (subscriptionType === "group") {
      const select = document.querySelector(`#group-${id}`);
      if (!select || !select.value) {
        alert("Для складчины необходимо выбрать группу файлов!");
        return;
      }
      groupId = parseInt(select.value);
    }

    const formData = new FormData();
    if (groupId) {
      formData.append("group_id", groupId);
    }

    const res = await authFetch(`${API_BASE_URL}/admin/requests/${id}/approve`, {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Ошибка: ${res.status} - ${errorText}`);
    }
    
    const result = await res.json();
    alert(`Заявка одобрена! ${result.message || ''}`);
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
