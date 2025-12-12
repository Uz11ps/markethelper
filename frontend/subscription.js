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

// 📡 Загрузка всех подписок (активных и неактивных)
async function loadSubscriptions() {
  try {
    const res = await authFetch(API_SUBS);
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    allSubs = await res.json();
    
    // Добавляем информацию о количестве продлений для каждого пользователя
    const userSubsCount = {};
    allSubs.forEach(sub => {
      const userId = sub.user_id || sub.tg_id;
      if (userId) {
        if (!userSubsCount[userId]) {
          userSubsCount[userId] = {
            count: 0,
            username: sub.username,
            tg_id: sub.tg_id
          };
        }
        userSubsCount[userId].count++;
      }
    });
    
    // Добавляем количество продлений к каждой подписке
    allSubs = allSubs.map(sub => {
      const userId = sub.user_id || sub.tg_id;
      const userInfo = userSubsCount[userId] || { count: 1 };
      return {
        ...sub,
        renewals_count: userInfo.count,
        is_active: new Date(sub.end_date) > new Date()
      };
    });
    
    applyFilters();
  } catch (err) {
    console.error("Ошибка загрузки подписок:", err);
    document.querySelector("#subsTable tbody").innerHTML = `
      <tr><td colspan="10">❌ Ошибка загрузки подписок</td></tr>
    `;
  }
}

// 🖨️ Отрисовка таблицы
function renderTable(data) {
  const tbody = document.querySelector("#subsTable tbody");
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11">📭 Подписок не найдено</td></tr>`;
    return;
  }

  data.forEach(item => {
    const row = document.createElement("tr");
    const isActive = item.is_active !== undefined ? item.is_active : (new Date(item.end_date) > new Date());
    const statusBadge = isActive 
      ? '<span style="color: #2ea44f; font-weight: 600;">✓ Активна</span>'
      : '<span style="color: #e8616b; font-weight: 600;">✗ Неактивна</span>';
    
    const renewalsBadge = item.renewals_count > 1 
      ? `<span style="background: #494f5e; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 5px;" title="Количество продлений">${item.renewals_count}x</span>`
      : '';

    row.innerHTML = `
      <td>${item.id}</td>
      <td>
        ${item.username
          ? `<a href="https://t.me/${item.username}" target="_blank">@${item.username}</a>${renewalsBadge}`
          : `<span style="color:gray">ID: ${item.tg_id || item.user_id || '—'}</span>${renewalsBadge}`}
      </td>
      <td>${item.tariff_id || "—"}</td>
      <td>${statusBadge}</td>
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

// 🔍 Применение фильтров и поиска
function applyFilters() {
  const statusFilter = document.getElementById("statusFilter")?.value || "all";
  const searchQuery = (document.getElementById("searchInput")?.value || "").toLowerCase();
  
  let filtered = [...allSubs];
  
  // Фильтр по статусу
  if (statusFilter === "active") {
    filtered = filtered.filter(sub => sub.is_active);
  } else if (statusFilter === "inactive") {
    filtered = filtered.filter(sub => !sub.is_active);
  }
  
  // Поиск по username или файлу
  if (searchQuery) {
    filtered = filtered.filter(sub => {
      const usernameMatch = (sub.username || "").toLowerCase().includes(searchQuery);
      const fileMatch = (sub.file_name || "").toLowerCase().includes(searchQuery);
      const tgIdMatch = String(sub.tg_id || "").includes(searchQuery);
      return usernameMatch || fileMatch || tgIdMatch;
    });
  }
  
  renderTable(filtered);
}

// 🔍 Поиск по username и файлу
document.getElementById("searchInput")?.addEventListener("input", () => {
  applyFilters();
});

// 🔍 Фильтр по статусу
document.getElementById("statusFilter")?.addEventListener("change", () => {
  applyFilters();
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

// 🔧 Открыть модальное окно редактирования баланса
function openBalanceModal(userId, username, bonusBalance, tokenBalance) {
  currentUserId = userId;
  document.getElementById('balanceUsername').textContent = username || `ID: ${userId}`;
  document.getElementById('balanceType').value = 'bonus';
  document.getElementById('balanceAmount').value = bonusBalance || 0;
  document.getElementById('balanceModal').style.display = 'block';
}

// ❌ Закрыть модальное окно редактирования баланса
function closeBalanceModal() {
  document.getElementById('balanceModal').style.display = 'none';
  currentUserId = null;
}

// ✅ Подтвердить изменение баланса
async function confirmBalanceUpdate() {
  const balanceType = document.getElementById('balanceType').value;
  const amount = parseInt(document.getElementById('balanceAmount').value);

  if (isNaN(amount) || amount < 0) {
    showMessage('Введите корректное значение баланса', 'error');
    return;
  }

  if (!currentUserId) {
    showMessage('Ошибка: не указан ID пользователя', 'error');
    return;
  }

  try {
    const endpoint = balanceType === 'bonus' 
      ? `${API_USERS}/${currentUserId}/bonus`
      : `${API_USERS}/${currentUserId}/tokens`;
    
    const response = await authFetch(endpoint, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(
        balanceType === 'bonus' 
          ? { bonus_amount: amount }
          : { tokens: amount }
      )
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error('Ошибка обновления баланса: ' + errorText);
    }

    const result = await response.json();
    showMessage(`Баланс успешно обновлен! Новый баланс: ${result.new_balance || result.bonus_balance || amount}`, 'success');
    closeBalanceModal();
    loadSubscriptions();
  } catch (error) {
    showMessage('Ошибка: ' + error.message, 'error');
  }
}

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
  const extendModal = document.getElementById('extendModal');
  const balanceModal = document.getElementById('balanceModal');
  if (event.target === extendModal) {
    closeExtendModal();
  }
  if (event.target === balanceModal) {
    closeBalanceModal();
  }
}

// 🚀 Инициализация
loadSubscriptions();
