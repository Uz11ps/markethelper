// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const API_BONUSES = `${API_BASE_URL}/admin/bonuses`;

// Загрузка бонусов при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadBonuses();
});

// Загрузка списка ожидающих бонусов
async function loadBonuses() {
  try {
    const res = await authFetch(`${API_BONUSES}/pending`);
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    
    const bonuses = await res.json();
    renderBonusesTable(bonuses);
  } catch (err) {
    console.error("Ошибка при загрузке бонусов:", err);
    const tbody = document.querySelector("#bonusesTable tbody");
    tbody.innerHTML = `<tr><td colspan="7">❌ Ошибка при загрузке бонусов</td></tr>`;
  }
}

// Отрисовка таблицы бонусов
function renderBonusesTable(bonuses) {
  const tbody = document.querySelector("#bonusesTable tbody");
  tbody.innerHTML = "";

  if (bonuses.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7">📭 Нет ожидающих подтверждения бонусов</td></tr>`;
    return;
  }

  bonuses.forEach(bonus => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${bonus.id}</td>
      <td>
        ${bonus.referrer_username 
          ? `<a href="https://t.me/${bonus.referrer_username}" target="_blank">@${bonus.referrer_username}</a>` 
          : `<span style="color: gray;">ID: ${bonus.referrer_tg_id}</span>`}
      </td>
      <td>
        ${bonus.referred_username 
          ? `<a href="https://t.me/${bonus.referred_username}" target="_blank">@${bonus.referred_username}</a>` 
          : `<span style="color: gray;">ID: ${bonus.referred_tg_id}</span>`}
      </td>
      <td><b>${bonus.bonus_amount}</b> токенов</td>
      <td>${bonus.request_id ? `#${bonus.request_id}` : '—'}</td>
      <td>${bonus.created_at ? new Date(bonus.created_at).toLocaleDateString() : '—'}</td>
      <td>
        <button onclick="approveBonus(${bonus.id})" class="btn-small btn-primary">✅ Подтвердить</button>
        <button onclick="rejectBonus(${bonus.id})" class="btn-small btn-danger">❌ Отклонить</button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// Подтверждение бонуса
async function approveBonus(bonusId) {
  if (!confirm(`Подтвердить начисление бонуса #${bonusId}?`)) {
    return;
  }

  try {
    const res = await authFetch(`${API_BONUSES}/${bonusId}/approve`, {
      method: "POST"
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: await res.text() }));
      throw new Error(errorData.detail || `Ошибка: ${res.status}`);
    }

    const result = await res.json();
    alert(`✅ ${result.message}\nНовый баланс реферера: ${result.new_balance} токенов`);
    loadBonuses();
  } catch (err) {
    alert("❌ Ошибка: " + err.message);
  }
}

// Отклонение бонуса
async function rejectBonus(bonusId) {
  if (!confirm(`Отклонить бонус #${bonusId}?`)) {
    return;
  }

  try {
    const res = await authFetch(`${API_BONUSES}/${bonusId}/reject`, {
      method: "POST"
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: await res.text() }));
      throw new Error(errorData.detail || `Ошибка: ${res.status}`);
    }

    const result = await res.json();
    alert(`✅ ${result.message}`);
    loadBonuses();
  } catch (err) {
    alert("❌ Ошибка: " + err.message);
  }
}

