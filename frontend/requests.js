// Конфигурация API (используется из auth.js)
// const API_BASE_URL уже объявлен в auth.js

let groupsList = [];
let allRequestsData = []; // Храним все заявки для статистики

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  console.log("[DOMContentLoaded] Страница загружена");
  if (!requireAuth()) {
    console.error("[DOMContentLoaded] Аутентификация не пройдена");
    return;
  }
  console.log("[DOMContentLoaded] Загружаем группы и заявки...");
  loadGroups();
  loadRequests();
});

// Загрузка списка групп
async function loadGroups() {
  try {
    const res = await authFetch(`${API_BASE_URL}/admin/groups/`);
    if (res.ok) {
      groupsList = await res.json();
      console.log(`[loadGroups] Загружено групп: ${groupsList.length}`);
      if (groupsList.length === 0) {
        console.warn("[loadGroups] Список групп пуст! Создайте группы в разделе 'Группы'");
      }
    } else {
      const errorText = await res.text();
      console.error(`[loadGroups] Ошибка API: ${res.status} - ${errorText}`);
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
    console.log(`[loadRequests] Первые 3 заявки для отладки:`, data.slice(0, 3).map(r => ({ id: r.id, status: r.status })));
    
    // Сохраняем все заявки для статистики
    allRequestsData = data;

    // Показываем статистику - вызываем сразу после получения данных
    console.log(`[loadRequests] Вызываем renderStats с ${data.length} заявками`);
    
    // Убеждаемся, что DOM готов перед отрисовкой статистики
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => renderStats(data));
    } else {
      // DOM уже готов, можно сразу вызывать
      renderStats(data);
    }

    const tbody = document.querySelector("#requestsTable tbody");
    tbody.innerHTML = "";

    // Фильтруем только новые заявки
    const pending = data.filter(req => {
      console.log(`[loadRequests] Проверка заявки:`, req.id, `status="${req.status}"`);
      const status = req.status || "";
      return status === "Pending" || status === "В ожидании" || status.toLowerCase() === "pending";
    });
    
    console.log(`[loadRequests] Отфильтровано заявок со статусом "Pending":`, pending.length);

    if (pending.length === 0) {
      console.log(`[loadRequests] Нет заявок со статусом "Pending"`);
      if (data.length > 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px; color: var(--fg-muted);">
          <div style="font-size: 1.1rem; margin-bottom: 8px;">📋 Нет новых заявок</div>
          <div style="font-size: 0.9rem;">Все заявки обработаны</div>
        </td></tr>`;
      } else {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px; color: var(--fg-muted);">
          <div style="font-size: 1.1rem;">📭 Заявок пока нет</div>
        </td></tr>`;
      }
      return;
    }

    pending.forEach(req => {
      const row = document.createElement("tr");
      // Определяем тип подписки: если не указан явно, определяем по tariff_code
      let subscriptionType = req.subscription_type;
      if (!subscriptionType || subscriptionType === "group") {
        // Если tariff_code INDIVIDUAL, то это индивидуальный доступ
        if (req.tariff_code === "INDIVIDUAL") {
          subscriptionType = "individual";
        } else {
          subscriptionType = "group"; // По умолчанию складчина
        }
      }
      const typeLabel = subscriptionType === "individual" ? "👤 Индивидуальный" : "📦 Складчина";
      
      console.log(`[loadRequests] Заявка ${req.id}: tariff_code=${req.tariff_code}, subscription_type=${req.subscription_type}, определенный тип=${subscriptionType}`);
      
      // Для складчины показываем выбор группы, для индивидуального - не показываем
      let groupSelect = '';
      if (subscriptionType === "group") {
        if (groupsList.length === 0) {
          groupSelect = `
            <div style="color: red; font-size: 0.9em; margin-bottom: 5px;">
              ⚠️ Нет доступных групп! Создайте группы в разделе "Группы"
            </div>
          `;
        } else {
          groupSelect = `
            <select id="group-${req.id}" style="margin-bottom: 5px; width: 100%;" required>
              <option value="">-- Выберите группу --</option>
              ${groupsList.map(g => `<option value="${g.id}" ${g.id === req.group_id ? 'selected' : ''}>${g.name}</option>`).join('')}
            </select>
          `;
        }
      } else {
        groupSelect = `<span style="color: gray;">Индивидуальный доступ</span>`;
      }

      row.innerHTML = `
        <td>${req.id}</td>
        <td>
          ${req.username 
            ? `<a href="https://t.me/${req.username}" target="_blank">@${req.username}</a>` 
            : `<span style="color: gray;">ID: ${req.tg_id || '—'}</span>`}
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
    console.log(`[approve] Начало одобрения заявки ${id}, subscriptionType=${subscriptionType}`);
    
    // Проверяем, что subscriptionType корректный
    if (!subscriptionType || (subscriptionType !== "individual" && subscriptionType !== "group")) {
      console.error(`[approve] Некорректный subscriptionType: ${subscriptionType}`);
      // Пытаемся определить тип по tariff_code из заявки
      const req = allRequestsData.find(r => r.id === id);
      if (req && req.tariff_code === "INDIVIDUAL") {
        subscriptionType = "individual";
        console.log(`[approve] Исправлен subscriptionType на individual на основе tariff_code`);
      } else {
        subscriptionType = "group";
        console.log(`[approve] Исправлен subscriptionType на group по умолчанию`);
      }
    }
    
    let groupId = null;
    
    if (subscriptionType === "group") {
      // Проверяем, что есть доступные группы
      if (groupsList.length === 0) {
        alert("Ошибка: нет доступных групп! Пожалуйста, создайте группы в разделе 'Группы' перед одобрением заявки.");
        return;
      }
      
      const select = document.querySelector(`#group-${id}`);
      if (!select) {
        alert("Ошибка: не найден элемент выбора группы! Обновите страницу и попробуйте снова.");
        return;
      }
      const selectedValue = select.value;
      if (!selectedValue || selectedValue === "") {
        alert("Для складчины необходимо выбрать группу файлов из выпадающего списка!");
        return;
      }
      groupId = parseInt(selectedValue);
      if (isNaN(groupId) || groupId <= 0) {
        alert("Ошибка: выбранная группа имеет недопустимый ID! Обновите страницу и попробуйте снова.");
        return;
      }
    }

    const formData = new FormData();
    // Для складчины group_id обязателен, для индивидуального доступа не передаем
    if (subscriptionType === "group") {
      if (!groupId || isNaN(groupId) || groupId <= 0) {
        alert("Ошибка: для складчины необходимо указать group_id!");
        console.error(`[approve] Ошибка валидации: subscriptionType=${subscriptionType}, groupId=${groupId}`);
        return;
      }
      // FormData передает значения как строки, но бэкенд ожидает int
      formData.append("group_id", String(groupId));
      console.log(`[approve] Отправка group_id=${groupId} (тип: ${typeof groupId}) для заявки ${id}`);
    } else {
      console.log(`[approve] Индивидуальный доступ, group_id не требуется для заявки ${id}`);
    }

    // Логируем содержимое FormData для отладки
    console.log(`[approve] FormData содержимое:`);
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}: ${value} (тип: ${typeof value})`);
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

// 📊 Отрисовка статистики по заявкам
function renderStats(data) {
  console.log("[renderStats] === НАЧАЛО ФУНКЦИИ ===");
  console.log("[renderStats] Данные:", data);
  console.log("[renderStats] Тип данных:", typeof data, Array.isArray(data));
  console.log("[renderStats] Состояние DOM:", document.readyState);
  
  const statsContainer = document.getElementById("requestsStats");
  if (!statsContainer) {
    console.error("[renderStats] ❌ Контейнер requestsStats не найден!");
    console.error("[renderStats] Все элементы с id:", Array.from(document.querySelectorAll('[id]')).map(el => el.id));
    // Попробуем найти через querySelector
    const altContainer = document.querySelector('#requestsStats');
    if (altContainer) {
      console.log("[renderStats] ✅ Контейнер найден через querySelector");
      _renderStatsContent(altContainer, data);
    }
    return;
  }
  
  console.log("[renderStats] ✅ Контейнер найден:", statsContainer);
  console.log("[renderStats] Контейнер видим:", statsContainer.offsetHeight > 0);
  
  _renderStatsContent(statsContainer, data);
}

function _renderStatsContent(statsContainer, data) {
  console.log("[_renderStatsContent] Начало отрисовки контента");
  
  // Проверяем, что данные - массив
  if (!Array.isArray(data)) {
    console.error("[_renderStatsContent] Данные не являются массивом:", typeof data, data);
    statsContainer.innerHTML = `<div style="color: red; padding: 20px;">Ошибка: данные не являются массивом</div>`;
    return;
  }
  
  // Подсчитываем статистику
  const total = data.length;
  
  // Проверяем все возможные варианты статусов
  const uniqueStatuses = [...new Set(data.map(r => r.status))];
  console.log("[renderStats] Уникальные статусы:", uniqueStatuses);
  console.log("[renderStats] Примеры статусов из данных:", data.slice(0, 5).map(r => ({ id: r.id, status: r.status })));
  
  const pending = data.filter(req => {
    const status = String(req.status || "").toLowerCase();
    return status === "pending" || status === "в ожидании" || status.includes("ожида");
  }).length;
  
  const approved = data.filter(req => {
    const status = String(req.status || "").toLowerCase();
    return status === "approved" || status === "одобрена" || status.includes("одобр");
  }).length;
  
  const rejected = data.filter(req => {
    const status = String(req.status || "").toLowerCase();
    return status === "rejected" || status === "отклонена" || status.includes("отклон");
  }).length;
  
  console.log("[renderStats] Подсчет:", { total, pending, approved, rejected });
  
  // Вычисляем проценты
  const pendingPercent = total > 0 ? Math.round((pending / total) * 100) : 0;
  const approvedPercent = total > 0 ? Math.round((approved / total) * 100) : 0;
  const rejectedPercent = total > 0 ? Math.round((rejected / total) * 100) : 0;
  
  // Вычисляем углы для круговой диаграммы
  const approvedAngle = (approved / total) * 360;
  const rejectedAngle = (rejected / total) * 360;
  const pendingAngle = (pending / total) * 360;
  
  // Создаем SVG для круговой диаграммы
  const svgSize = 120;
  const radius = svgSize / 2 - 10;
  const center = svgSize / 2;
  
  let currentAngle = -90; // Начинаем сверху
  const approvedEndAngle = currentAngle + approvedAngle;
  const rejectedEndAngle = approvedEndAngle + rejectedAngle;
  
  // Функция для преобразования угла в координаты
  const getCoordinates = (angle, r) => {
    const rad = (angle * Math.PI) / 180;
    return {
      x: center + r * Math.cos(rad),
      y: center + r * Math.sin(rad)
    };
  };
  
  const approvedStart = getCoordinates(currentAngle, radius);
  currentAngle += approvedAngle;
  const approvedEnd = getCoordinates(currentAngle, radius);
  
  const rejectedStart = getCoordinates(currentAngle, radius);
  currentAngle += rejectedAngle;
  const rejectedEnd = getCoordinates(currentAngle, radius);
  
  const pendingStart = getCoordinates(currentAngle, radius);
  currentAngle += pendingAngle;
  const pendingEnd = getCoordinates(currentAngle, radius);
  
  // Создаем пути для секторов
  const largeArcFlag = (angle) => angle > 180 ? 1 : 0;
  
  const approvedPath = approved > 0 ? `
    M ${center} ${center}
    L ${approvedStart.x} ${approvedStart.y}
    A ${radius} ${radius} 0 ${largeArcFlag(approvedAngle)} 1 ${approvedEnd.x} ${approvedEnd.y}
    Z
  ` : '';
  
  const rejectedPath = rejected > 0 ? `
    M ${center} ${center}
    L ${rejectedStart.x} ${rejectedStart.y}
    A ${radius} ${radius} 0 ${largeArcFlag(rejectedAngle)} 1 ${rejectedEnd.x} ${rejectedEnd.y}
    Z
  ` : '';
  
  const pendingPath = pending > 0 ? `
    M ${center} ${center}
    L ${pendingStart.x} ${pendingStart.y}
    A ${radius} ${radius} 0 ${largeArcFlag(pendingAngle)} 1 ${pendingEnd.x} ${pendingEnd.y}
    Z
  ` : '';
  
  // Проверяем, что контейнер существует перед вставкой
  if (!statsContainer) {
    console.error("[renderStats] Контейнер не найден после проверки!");
    return;
  }
  
  console.log("[renderStats] Создаем HTML для статистики...");
  
  statsContainer.innerHTML = `
    <div class="stat-card total">
      <div class="stat-card-icon">📊</div>
      <div class="stat-card-title">Всего заявок</div>
      <div class="stat-card-value">${total}</div>
    </div>
    <div class="stat-card pending">
      <div class="stat-card-icon">⏳</div>
      <div class="stat-card-title">В ожидании</div>
      <div class="stat-card-value">${pending}</div>
      <div class="stat-card-percentage">${pendingPercent}%</div>
    </div>
    <div class="stat-card approved">
      <div class="stat-card-icon">✅</div>
      <div class="stat-card-title">Одобрено</div>
      <div class="stat-card-value">${approved}</div>
      <div class="stat-card-percentage">${approvedPercent}%</div>
    </div>
    <div class="stat-card rejected">
      <div class="stat-card-icon">❌</div>
      <div class="stat-card-title">Отклонено</div>
      <div class="stat-card-value">${rejected}</div>
      <div class="stat-card-percentage">${rejectedPercent}%</div>
    </div>
    <div class="stat-card chart-card" style="grid-column: span 2;">
      <div class="stat-card-title" style="margin-bottom: 16px;">📈 Распределение заявок</div>
      <div style="display: flex; align-items: center; justify-content: center; gap: 30px; flex-wrap: wrap;">
        <div style="position: relative;">
          <svg width="${svgSize}" height="${svgSize}" style="transform: rotate(0deg);">
            ${approvedPath ? `<path d="${approvedPath}" fill="#2ea44f" stroke="var(--surface)" stroke-width="2"></path>` : ''}
            ${rejectedPath ? `<path d="${rejectedPath}" fill="#e8616b" stroke="var(--surface)" stroke-width="2"></path>` : ''}
            ${pendingPath ? `<path d="${pendingPath}" fill="#ffa500" stroke="var(--surface)" stroke-width="2"></path>` : ''}
            <circle cx="${center}" cy="${center}" r="${radius - 20}" fill="var(--surface)"></circle>
            <text x="${center}" y="${center}" text-anchor="middle" dominant-baseline="middle" fill="var(--fg)" font-size="24" font-weight="700">${total}</text>
          </svg>
        </div>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 16px; height: 16px; background: #2ea44f; border-radius: 3px;"></div>
            <span style="color: var(--fg-muted); font-size: 14px;">Одобрено: <strong style="color: var(--fg);">${approved}</strong> (${approvedPercent}%)</span>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 16px; height: 16px; background: #e8616b; border-radius: 3px;"></div>
            <span style="color: var(--fg-muted); font-size: 14px;">Отклонено: <strong style="color: var(--fg);">${rejected}</strong> (${rejectedPercent}%)</span>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 16px; height: 16px; background: #ffa500; border-radius: 3px;"></div>
            <span style="color: var(--fg-muted); font-size: 14px;">В ожидании: <strong style="color: var(--fg);">${pending}</strong> (${pendingPercent}%)</span>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Убеждаемся, что контейнер виден
  statsContainer.style.display = "grid";
  statsContainer.style.visibility = "visible";
  statsContainer.style.opacity = "1";
  
  console.log("[renderStats] Статистика отображена:", { total, pending, approved, rejected });
  console.log("[renderStats] Контейнер после вставки:", statsContainer.innerHTML.substring(0, 200));
  console.log("[renderStats] Контейнер видим:", statsContainer.offsetHeight > 0);
}

// Убираем вызов loadRequests() отсюда, так как он вызывается в DOMContentLoaded
