const API_URL = 'http://localhost:8000/admin';

// Загрузка настроек при открытии страницы
document.addEventListener('DOMContentLoaded', loadSettings);

async function loadSettings() {
  try {
    const response = await fetch(`${API_URL}/settings`);
    if (!response.ok) throw new Error('Ошибка загрузки настроек');

    const data = await response.json();

    document.getElementById('aiPrompt').value = data.ai_prompt;
    document.getElementById('referralBonus').value = data.referral_bonus;
  } catch (error) {
    showMessage('Ошибка загрузки настроек: ' + error.message, 'error');
  }
}

async function saveSettings() {
  const aiPrompt = document.getElementById('aiPrompt').value;
  const referralBonus = parseInt(document.getElementById('referralBonus').value);

  if (!aiPrompt.trim()) {
    showMessage('Промпт не может быть пустым', 'error');
    return;
  }

  if (isNaN(referralBonus) || referralBonus < 0) {
    showMessage('Некорректное значение бонуса', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_URL}/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ai_prompt: aiPrompt,
        referral_bonus: referralBonus
      })
    });

    if (!response.ok) throw new Error('Ошибка сохранения настроек');

    const result = await response.json();
    showMessage('Настройки успешно сохранены', 'success');
  } catch (error) {
    showMessage('Ошибка сохранения: ' + error.message, 'error');
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
