const API_HOST = `${window.location.protocol}//${window.location.hostname}:8000`;
const API_URL = `${API_HOST}/admin`;

// Загрузка настроек при открытии страницы
document.addEventListener('DOMContentLoaded', loadSettings);

async function loadSettings() {
  try {
    const response = await fetch(`${API_URL}/settings`);
    if (!response.ok) throw new Error('Ошибка загрузки настроек');

    const data = await response.json();

    document.getElementById('aiPrompt').value = data.ai_prompt || '';
    document.getElementById('imagePrompt').value = data.prompt_generator_prompt || '';
    document.getElementById('referralBonus').value = data.referral_bonus ?? '';
    document.getElementById('imageCost').value = data.image_generation_cost ?? '';
    document.getElementById('gptCost').value = data.gpt_request_cost ?? '';
  } catch (error) {
    showMessage('Ошибка загрузки настроек: ' + error.message, 'error');
  }
}

async function saveSettings() {
  const aiPrompt = document.getElementById('aiPrompt').value;
  const imagePrompt = document.getElementById('imagePrompt').value;
  const referralBonus = parseInt(document.getElementById('referralBonus').value);
  const imageCost = parseInt(document.getElementById('imageCost').value);
  const gptCost = parseInt(document.getElementById('gptCost').value);

  if (!aiPrompt.trim()) {
    showMessage('Промпт не может быть пустым', 'error');
    return;
  }

  if (!imagePrompt.trim()) {
    showMessage('Промпт генератора изображений не может быть пустым', 'error');
    return;
  }

  if (isNaN(referralBonus) || referralBonus < 0) {
    showMessage('Некорректное значение бонуса', 'error');
    return;
  }

  if (isNaN(imageCost) || imageCost < 0) {
    showMessage('Некорректная стоимость генерации изображения', 'error');
    return;
  }

  if (isNaN(gptCost) || gptCost < 0) {
    showMessage('Некорректная стоимость запроса к GPT', 'error');
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
        prompt_generator_prompt: imagePrompt,
        referral_bonus: referralBonus,
        image_generation_cost: imageCost,
        gpt_request_cost: gptCost
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
