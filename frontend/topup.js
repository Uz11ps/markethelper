// Конфигурация API
const API_TOPUP = `${API_BASE_URL}/admin/tokens/purchases`;
let currentPurchaseId = null;

// Загрузка заявок на пополнение
async function loadTopupRequests() {
  try {
    const statusFilter = document.getElementById('statusFilter').value;
    let url = API_TOPUP;
    if (statusFilter) {
      url += `?status_filter=${statusFilter}`;
    }
    
    const res = await authFetch(url);
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    
    const requests = await res.json();
    renderTopupTable(requests);
  } catch (err) {
    console.error("Ошибка загрузки заявок:", err);
    document.querySelector("#topupTable tbody").innerHTML = `
      <tr><td colspan="9">❌ Ошибка загрузки заявок</td></tr>
    `;
  }
}

// Отрисовка таблицы заявок
function renderTopupTable(requests) {
  const tbody = document.querySelector("#topupTable tbody");
  tbody.innerHTML = "";

  if (requests.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9">📭 Заявок не найдено</td></tr>`;
    return;
  }

  requests.forEach(req => {
    const row = document.createElement("tr");
    const statusClass = {
      "PENDING": "status-pending",
      "APPROVED": "status-approved",
      "REJECTED": "status-rejected"
    }[req.status] || "";

    let actionsHtml = "";
    if (req.status === "PENDING") {
      actionsHtml = `
        <button onclick="openApproveModal(${req.id})" class="btn-small btn-primary">Одобрить</button>
        <button onclick="rejectTopup(${req.id})" class="btn-small btn-danger">Отклонить</button>
      `;
    } else {
      actionsHtml = `<span style="color: gray;">Обработано</span>`;
    }

    row.innerHTML = `
      <td>${req.id}</td>
      <td>
        ${req.username 
          ? `<a href="https://t.me/${req.username}" target="_blank">@${req.username}</a>` 
          : `ID: ${req.user_id}`}
        ${req.full_name ? `<br><small>${req.full_name}</small>` : ''}
      </td>
      <td><b>${req.amount}</b></td>
      <td><b>${req.cost}₽</b></td>
      <td class="${statusClass}">${req.status}</td>
      <td>${req.payment_method || '—'}</td>
      <td>${new Date(req.created_at).toLocaleString('ru-RU')}</td>
      <td>${req.processed_at ? new Date(req.processed_at).toLocaleString('ru-RU') : '—'}</td>
      <td class="actions">${actionsHtml}</td>
    `;
    tbody.appendChild(row);
  });
}

// Открытие модального окна одобрения
function openApproveModal(purchaseId) {
  currentPurchaseId = purchaseId;
  document.getElementById('approvePurchaseId').textContent = purchaseId;
  document.getElementById('paymentMethod').value = '';
  document.getElementById('approveModal').style.display = 'block';
}

// Закрытие модального окна одобрения
function closeApproveModal() {
  document.getElementById('approveModal').style.display = 'none';
  currentPurchaseId = null;
}

// Подтверждение одобрения
async function confirmApprove() {
  const paymentMethod = document.getElementById('paymentMethod').value.trim();
  
  try {
    const payload = {};
    if (paymentMethod) {
      payload.payment_method = paymentMethod;
    }
    
    const res = await authFetch(`${API_TOPUP}/${currentPurchaseId}/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Ошибка: ${res.status} - ${errorText}`);
    }

    const result = await res.json();
    alert(`✅ ${result.message}\n\nТокены начислены: ${result.tokens_added}\nНовый баланс: ${result.new_balance}`);
    closeApproveModal();
    loadTopupRequests();
  } catch (err) {
    console.error('Ошибка одобрения:', err);
    alert('❌ Ошибка: ' + err.message);
  }
}

// Отклонение заявки
async function rejectTopup(purchaseId) {
  if (!confirm(`Отклонить заявку #${purchaseId}?`)) {
    return;
  }

  try {
    const res = await authFetch(`${API_TOPUP}/${purchaseId}/reject`, {
      method: 'POST'
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Ошибка: ${res.status} - ${errorText}`);
    }

    const result = await res.json();
    alert(`✅ ${result.message}`);
    loadTopupRequests();
  } catch (err) {
    console.error('Ошибка отклонения:', err);
    alert('❌ Ошибка: ' + err.message);
  }
}

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
  const modal = document.getElementById('approveModal');
  if (event.target === modal) {
    closeApproveModal();
  }
}

