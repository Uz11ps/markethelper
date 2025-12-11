// Конфигурация API
// Для продакшена замените на: const API_BASE_URL = 'https://374504.vm.spacecore.network/api';
const API_BASE_URL = window.location.origin + '/api';

// Управление токеном аутентификации
const TOKEN_KEY = 'admin_token';

/**
 * Сохранение токена в localStorage
 */
function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Получение токена из localStorage
 */
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Удаление токена
 */
function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Проверка аутентификации
 */
function isAuthenticated() {
  return !!getToken();
}

/**
 * Вход в систему
 */
async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/admin/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка входа' }));
    throw new Error(error.detail || 'Неверное имя пользователя или пароль');
  }

  const data = await response.json();
  saveToken(data.access_token);
  return data;
}

/**
 * Выход из системы
 */
function logout() {
  removeToken();
  window.location.href = '/login.html';
}

/**
 * Получение заголовков с токеном для API запросов
 */
function getAuthHeaders() {
  const token = getToken();
  if (!token) {
    throw new Error('Не авторизован');
  }
  return {
    'Authorization': `Bearer ${token}`,
  };
}

/**
 * Проверка аутентификации и редирект на логин если не авторизован
 */
function requireAuth() {
  if (!isAuthenticated()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

/**
 * Проверка токена и получение данных текущего админа
 */
async function getCurrentAdmin() {
  const token = getToken();
  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      removeToken();
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Ошибка проверки токена:', error);
    removeToken();
    return null;
  }
}

/**
 * Обертка для fetch с автоматической обработкой ошибок аутентификации
 */
async function authFetch(url, options = {}) {
  const authHeaders = getAuthHeaders();
  const headers = {
    ...authHeaders,
    ...options.headers,
  };
  
  // Если body является FormData, не устанавливаем Content-Type
  // Браузер автоматически установит multipart/form-data с boundary
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  } else if (!headers['Content-Type']) {
    // Для JSON запросов устанавливаем Content-Type, если он не указан
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeToken();
    window.location.href = '/login.html';
    throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
  }

  return response;
}

