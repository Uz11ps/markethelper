// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const API_SUBS = `${API_BASE_URL}/admin/requests/subscriptions`;
const API_ADMIN = `${API_BASE_URL}/admin`;
const API_USERS = `${API_BASE_URL}/admin/users`;
let allSubs = [];
let currentSubId = null;
let currentUserId = null;

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadSubscriptions();
});

// 📡 Загрузка всех активных подписок
async function loadSubscriptions() {
  try {
    const res = await authFetch(API_SUBS);
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    allSubs = await res.json();
    renderTable(allSubs);
  } catch (err) {
    console.error("Ошибка загрузки подписок:", err);
    document.querySelector("#subsTable tbody").innerHTML = `
      <tr><td colspan="8">❌ Ошибка загрузки подписок</td></tr>
    `;
  }
}

// 🖨️ Отрисовка таблицы
function renderTable(data) {
  const tbody = document.querySelector("#subsTable tbody");
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10">📭 Подписок не найдено</td></tr>`;
    return;
  }

  data.forEach(item => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${item.id}</td>
      <td>
        ${item.username
          ? `<a href="https://t.me/${item.username}" target="_blank">@${item.username}</a>`
          : `<span style="color:gray">нет username</span>`}
      </td>
      <td>${item.tariff_id || "—"}</td>
      <td>${item.status_id || "—"}</td>
      <td>${new Date(item.start_date).toLocaleDateString()}</td>
      <td>${new Date(item.end_date).toLocaleDateString()}</td>
      <td>${item.group || "—"}</td>
      <td>${item.file_name || "—"}</td>
      <td>
        💰 ${item.bonus_balance || 0} токенов
        ${item.user_id ? `<br><button onclick="openBalanceModal(${item.user_id}, '${item.username || 'пользователь'}', ${item.bonus_balance || 0}, ${item.token_balance || 0})" class="btn-small btn-secondary" style="margin-top: 5px; font-size: 11px;">Изменить</button>` : ''}
      </td>
      <td class="actions">
        <button onclick="openExtendModal(${item.id})" class="btn-small btn-primary">Продлить</button>
        <button onclick="revokeSubscription(${item.id})" class="btn-small btn-danger">Отозвать</button>
      </td>
    `;

    tbody.appendChild(row);
  });
}

// 🔍 Поиск по названию файла
document.getElementById("searchFile").addEventListener("input", e => {
  const query = e.target.value.toLowerCase();
  const filtered = allSubs.filter(sub =>
    (sub.file_name || "").toLowerCase().includes(query)
  );
  renderTable(filtered);
});

// 📢 Рассылка сообщений
async function sendBroadcast() {
  const message = document.getElementById('broadcastMessage').value;
  const audience = document.getElementById('broadcastAudience').value;

  if (!message.trim()) {
    showMessage('Введите текст сообщения', 'error');
    return;
  }

  if (!confirm(`Отправить сообщение аудитории: ${audience}?`)) {
    return;
  }

  try {
    const response = await authFetch(`${API_ADMIN}/broadcast/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        target: audience  // Используем target вместо audience
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Ошибка рассылки:', errorText);
      throw new Error('Ошибка отправки рассылки: ' + errorText);
    }

    const result = await response.json();
    const sentCount = result.sent_count || result.total_users || 0;
    showMessage(`Рассылка отправлена! Получатели: ${sentCount}`, 'success');
    document.getElementById('broadcastMessage').value = '';
  } catch (error) {
    showMessage('Ошибка: ' + error.message, 'error');
  }
}

// 🔧 Открыть модальное окно продления
function openExtendModal(subId) {
  currentSubId = subId;
  document.getElementById('extendSubId').textContent = subId;
  document.getElementById('extendModal').style.display = 'block';
}

// ❌ Закрыть модальное окно
function closeExtendModal() {
  document.getElementById('extendModal').style.display = 'none';
  currentSubId = null;
}

// ✅ Подтвердить продление
async function confirmExtend() {
  const days = parseInt(document.getElementById('extendDays').value);

  if (isNaN(days) || days < 1) {
    showMessage('Введите корректное количество дней', 'error');
    return;
  }

  try {
    const response = await authFetch(`${API_ADMIN}/subscriptions/${currentSubId}/extend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ days: days })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Ошибка продления:', errorText);
      throw new Error('Ошибка продления подписки: ' + errorText);
    }

    const result = await response.json();
    showMessage(result.message, 'success');
    closeExtendModal();
    loadSubscriptions();
  } catch (error) {
    showMessage('Ошибка: ' + error.message, 'error');
  }
}

// 🗑️ Отозвать подписку
async function revokeSubscription(subId) {
  if (!confirm(`Отозвать подписку #${subId}?`)) {
    return;
  }

  try {
    const response = await authFetch(`${API_ADMIN}/subscriptions/${subId}`, {
      method: 'DELETE'
    });

    if (!response.ok) throw new Error('Ошибка отзыва подписки');

    const result = await response.json();
    showMessage(result.message, 'success');
    loadSubscriptions();
  } catch (error) {
    showMessage('Ошибка: ' + error.message, 'error');
  }
}

// 💬 Показать сообщение
function showMessage(text, type) {
  const messageEl = document.getElementById('message');
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
  messageEl.style.display = 'block';

  setTimeout(() => {
    messageEl.style.display = 'none';
  }, 3000);
}

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
  const modal = document.getElementById('extendModal');
  if (event.target === modal) {
    closeExtendModal();
  }
}

// 🚀 Инициализация
loadSubscriptions();
