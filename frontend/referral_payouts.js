// Конфигурация API (API_BASE_URL уже объявлен в auth.js)

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadPayouts();
});

async function loadPayouts() {
  try {
    const response = await authFetch(`${API_BASE_URL}/admin/referral-payouts/`);
    if (!response.ok) throw new Error('Ошибка загрузки выплат');
    
    const payouts = await response.json();
    renderPayouts(payouts);
  } catch (error) {
    showMessage('Ошибка загрузки выплат: ' + error.message, 'error');
  }
}

function renderPayouts(payouts) {
  const tbody = document.getElementById('payouts-tbody');
  
  if (payouts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7">Нет заявок на выплату</td></tr>';
    return;
  }
  
  tbody.innerHTML = payouts.map(payout => {
    const statusClass = {
      'PENDING': 'status-pending',
      'APPROVED': 'status-approved',
      'REJECTED': 'status-rejected'
    }[payout.status] || '';
    
    const statusText = {
      'PENDING': 'Ожидает',
      'APPROVED': 'Одобрена',
      'REJECTED': 'Отклонена'
    }[payout.status] || payout.status;
    
    const createdDate = payout.created_at ? new Date(payout.created_at).toLocaleString('ru-RU') : '—';
    
    const actions = payout.status === 'PENDING' ? `
      <button onclick="approvePayout(${payout.id})" class="btn-success">✅ Одобрить</button>
      <button onclick="rejectPayout(${payout.id})" class="btn-danger">❌ Отклонить</button>
    ` : `
      <span class="text-muted">Обработано</span>
      ${payout.admin_comment ? `<br><small>${payout.admin_comment}</small>` : ''}
    `;
    
    return `
      <tr>
        <td>${payout.id}</td>
        <td>
          ${payout.referrer_full_name || payout.referrer_username || '—'}<br>
          <small>@${payout.referrer_username || '—'}</small><br>
          <small>TG ID: ${payout.referrer_tg_id}</small>
        </td>
        <td>${payout.referral_count}</td>
        <td><strong>${payout.amount_rub.toFixed(2)}₽</strong></td>
        <td><span class="${statusClass}">${statusText}</span></td>
        <td>${createdDate}</td>
        <td>${actions}</td>
      </tr>
    `;
  }).join('');
}

async function approvePayout(payoutId) {
  const comment = prompt('Комментарий (необязательно):');
  if (comment === null) return; // Пользователь отменил
  
  try {
    const response = await authFetch(`${API_BASE_URL}/admin/referral-payouts/${payoutId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment: comment || null })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка подтверждения выплаты');
    }
    
    showMessage('Выплата одобрена', 'success');
    loadPayouts();
  } catch (error) {
    showMessage('Ошибка: ' + error.message, 'error');
  }
}

async function rejectPayout(payoutId) {
  const comment = prompt('Причина отклонения (обязательно):');
  if (!comment || comment.trim() === '') {
    alert('Необходимо указать причину отклонения');
    return;
  }
  
  try {
    const response = await authFetch(`${API_BASE_URL}/admin/referral-payouts/${payoutId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment: comment })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка отклонения выплаты');
    }
    
    showMessage('Выплата отклонена', 'success');
    loadPayouts();
  } catch (error) {
    showMessage('Ошибка: ' + error.message, 'error');
  }
}

function showMessage(text, type) {
  const messageEl = document.getElementById('message');
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
  messageEl.style.display = 'block';

  setTimeout(() => {
    messageEl.style.display = 'none';
  }, 3000);
}

