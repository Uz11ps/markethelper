// Конфигурация API (API_BASE_URL уже объявлен в auth.js)

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadSettings();
});

async function loadSettings() {
  try {
    // Загружаем промпты
    const promptsResponse = await authFetch(`${API_BASE_URL}/admin/settings/prompts`);
    if (!promptsResponse.ok) throw new Error('Ошибка загрузки промптов');
    const promptsData = await promptsResponse.json();

    document.getElementById('aiPrompt').value = promptsData.default_prompt || '';
    document.getElementById('imagePrompt').value = promptsData.product_analysis_prompt || '';

    // Загружаем все настройки для стоимости токенов и бонусов
    const settingsResponse = await authFetch(`${API_BASE_URL}/admin/settings/all`);
    if (!settingsResponse.ok) throw new Error('Ошибка загрузки настроек');
    const settingsData = await settingsResponse.json();

    document.getElementById('referralBonus').value = settingsData.referral_bonus?.value || '';
    document.getElementById('referralRubPerReferral').value = settingsData.referral_rub_per_referral?.value || '';
    document.getElementById('imageCost').value = settingsData.image_generation_cost?.value || '';
    document.getElementById('gptCost').value = settingsData.gpt_request_cost?.value || '';
    
    // Загружаем настройки канала
    const channelResponse = await authFetch(`${API_BASE_URL}/admin/settings/channel`);
    if (channelResponse.ok) {
      const channelData = await channelResponse.json();
      document.getElementById('channelUsername').value = channelData.channel_username || '';
      document.getElementById('channelBonus').value = channelData.channel_bonus || '';
    }
    
    // Загружаем настройки пополнения
    const topupResponse = await authFetch(`${API_BASE_URL}/admin/settings/topup`);
    if (topupResponse.ok) {
      const topupData = await topupResponse.json();
      document.getElementById('tokenPrice').value = topupData.token_price || '';
      
      const options = topupData.topup_options || [];
      if (options.length > 0) {
        document.getElementById('topupTokens1').value = options[0]?.tokens || '';
        document.getElementById('topupPrice1').value = options[0]?.price || '';
      }
      if (options.length > 1) {
        document.getElementById('topupTokens2').value = options[1]?.tokens || '';
        document.getElementById('topupPrice2').value = options[1]?.price || '';
      }
      if (options.length > 2) {
        document.getElementById('topupTokens3').value = options[2]?.tokens || '';
        document.getElementById('topupPrice3').value = options[2]?.price || '';
      }
      if (options.length > 3) {
        document.getElementById('topupTokens4').value = options[3]?.tokens || '';
        document.getElementById('topupPrice4').value = options[3]?.price || '';
      }
    }
  } catch (error) {
    showMessage('Ошибка загрузки настроек: ' + error.message, 'error');
  }
}

async function saveSettings() {
  const aiPrompt = document.getElementById('aiPrompt').value;
  const imagePrompt = document.getElementById('imagePrompt').value;
    const referralBonus = parseInt(document.getElementById('referralBonus').value);
    const referralReferrerBonus = parseInt(document.getElementById('referralReferrerBonus').value);
    const referralReferredTokens = parseInt(document.getElementById('referralReferredTokens').value);
    const referralRubPerReferral = parseFloat(document.getElementById('referralRubPerReferral').value);
  const imageCost = parseInt(document.getElementById('imageCost').value);
  const gptCost = parseInt(document.getElementById('gptCost').value);
  const gptModel = document.getElementById('gptModel').value;
  const imageModel = document.getElementById('imageModel').value;

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

  if (isNaN(referralReferrerBonus) || referralReferrerBonus < 0) {
    showMessage('Некорректное значение минимального бонуса реферера', 'error');
    return;
  }

  if (isNaN(referralReferredTokens) || referralReferredTokens < 0) {
    showMessage('Некорректное значение токенов для реферала', 'error');
    return;
  }

  if (!gptModel) {
    showMessage('Выберите GPT модель', 'error');
    return;
  }

  if (!imageModel) {
    showMessage('Выберите модель генерации изображений', 'error');
    return;
  }

  try {
    // Сохраняем промпты
    await authFetch(`${API_BASE_URL}/admin/settings/prompts/default`, {
      method: 'PUT',
      body: JSON.stringify({ template: aiPrompt }),
    });

    await authFetch(`${API_BASE_URL}/admin/settings/prompts/analysis`, {
      method: 'PUT',
      body: JSON.stringify({ template: imagePrompt }),
    });

    // Сохраняем стоимость токенов, бонусы и модели
    const settingsToUpdate = [
      { key: 'referral_bonus', value: referralBonus.toString(), description: 'Реферальный бонус за регистрацию' },
      { key: 'referral_referrer_bonus', value: referralReferrerBonus.toString(), description: 'Минимальный бонус реферера' },
      { key: 'referral_referred_tokens', value: referralReferredTokens.toString(), description: 'Токены для реферала при регистрации' },
      { key: 'referral_rub_per_referral', value: referralRubPerReferral.toString(), description: 'Рублей за одного реферала' },
      { key: 'image_generation_cost', value: imageCost.toString(), description: 'Стоимость генерации изображения в токенах' },
      { key: 'gpt_request_cost', value: gptCost.toString(), description: 'Стоимость запроса к GPT в токенах' },
      { key: 'gpt_model', value: gptModel, description: 'Модель GPT для запросов' },
      { key: 'image_model', value: imageModel, description: 'Модель для генерации изображений' },
    ];

    for (const setting of settingsToUpdate) {
      await authFetch(`${API_BASE_URL}/admin/settings/`, {
        method: 'POST',
        body: JSON.stringify(setting),
      });
    }
    
    // Сохраняем настройки пополнения
    const tokenPrice = parseFloat(document.getElementById('tokenPrice').value);
    if (!isNaN(tokenPrice) && tokenPrice >= 0) {
      await authFetch(`${API_BASE_URL}/admin/settings/topup/price`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: tokenPrice }),
      });
    }
    
    const topupOptions = [];
    for (let i = 1; i <= 4; i++) {
      const tokens = parseInt(document.getElementById(`topupTokens${i}`).value);
      const price = parseFloat(document.getElementById(`topupPrice${i}`).value);
      if (!isNaN(tokens) && !isNaN(price) && tokens > 0 && price > 0) {
        topupOptions.push({ tokens, price });
      }
    }
    
    if (topupOptions.length > 0) {
      await authFetch(`${API_BASE_URL}/admin/settings/topup/options`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ options: topupOptions }),
      });
    }

    showMessage('Настройки успешно сохранены', 'success');
  } catch (error) {
    showMessage('Ошибка сохранения: ' + error.message, 'error');
  }
}

async function saveChannelSettings() {
  const channelUsername = document.getElementById('channelUsername').value.trim();
  const channelBonus = parseInt(document.getElementById('channelBonus').value);

  if (isNaN(channelBonus) || channelBonus < 0) {
    showMessage('Некорректное значение бонуса за подписку', 'error');
    return;
  }

  try {
    await authFetch(`${API_BASE_URL}/admin/settings/channel/username`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: channelUsername })
    });

    await authFetch(`${API_BASE_URL}/admin/settings/channel/bonus`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bonus: channelBonus })
    });

    showMessage('Настройки канала успешно сохранены', 'success');
  } catch (error) {
    showMessage('Ошибка сохранения настроек канала: ' + error.message, 'error');
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
