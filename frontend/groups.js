// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const API_GROUPS = `${API_BASE_URL}/admin/groups`;

// Загрузка групп при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadGroups();
  
  // Инициализация формы создания группы
  const createForm = document.getElementById("createGroupForm");
  if (createForm) {
    createForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("groupName").value.trim();
      
      if (!name) {
        showMessage("Введите название группы", "error");
        return;
      }

      try {
        const res = await authFetch(API_GROUPS, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ name: name })
        });

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ detail: await res.text() }));
          throw new Error(errorData.detail || `Ошибка: ${res.status}`);
        }

        const result = await res.json();
        showMessage(`✅ Группа "${result.name}" успешно создана!`, "success");
        document.getElementById("groupName").value = "";
        // Обновляем список групп после создания
        await loadGroups();
      } catch (err) {
        showMessage("❌ Ошибка: " + err.message, "error");
      }
    });
  }
});

// Загрузка списка групп
async function loadGroups() {
  try {
    console.log("Загрузка групп из:", API_GROUPS);
    const res = await authFetch(API_GROUPS);
    if (!res.ok) {
      const errorText = await res.text();
      console.error("Ошибка API:", res.status, errorText);
      throw new Error(`Ошибка: ${res.status} - ${errorText}`);
    }
    
    const groups = await res.json();
    console.log("Получено групп:", groups.length, groups);
    await renderGroupsTable(groups);
  } catch (err) {
    console.error("Ошибка при загрузке групп:", err);
    const tbody = document.querySelector("#groupsTable tbody");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="5">❌ Ошибка при загрузке групп: ${err.message}</td></tr>`;
    }
  }
}

// Отрисовка таблицы групп
async function renderGroupsTable(groups) {
  const tbody = document.querySelector("#groupsTable tbody");
  tbody.innerHTML = "";

  if (groups.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5">📭 Групп не найдено</td></tr>`;
    return;
  }

  // Загружаем файлы для каждой группы
  for (const group of groups) {
    try {
      const filesRes = await authFetch(`${API_BASE_URL}/admin/files/group/${group.id}`);
      const files = filesRes.ok ? await filesRes.json() : [];
      group.files = files || [];
    } catch (err) {
      console.error(`Ошибка загрузки файлов для группы ${group.id}:`, err);
      group.files = [];
    }

    const row = document.createElement("tr");
    const filesCount = group.files ? group.files.length : 0;
    const filesList = group.files && group.files.length > 0 
      ? group.files.map(f => {
          const filename = f.filename || (f.path ? f.path.split('/').pop() : '—');
          return filename;
        }).join(', ')
      : 'Нет файлов';
    
    // Экранируем кавычки в названии группы для безопасного использования в onclick
    const safeGroupName = (group.name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    
    row.innerHTML = `
      <td>${group.id}</td>
      <td><b>${group.name}</b></td>
      <td>
        <span style="font-size: 0.9em;">${filesCount} файл(ов)</span><br>
        <span style="font-size: 0.8em; color: #666;">${filesList}</span>
      </td>
      <td>${group.created_at ? new Date(group.created_at).toLocaleDateString() : '—'}</td>
      <td>
        <button onclick="openFileModal(${group.id})" class="btn-small btn-secondary">📁 Загрузить файл</button>
        <button onclick="openEditModal(${group.id}, '${safeGroupName}')" class="btn-small btn-primary">✏️ Редактировать</button>
        <button onclick="deleteGroup(${group.id})" class="btn-small btn-danger">🗑️ Удалить</button>
      </td>
    `;
    tbody.appendChild(row);
  }
}

// Обработчик формы создания группы уже добавлен в DOMContentLoaded

// Открытие модального окна редактирования
function openEditModal(groupId, groupName) {
  document.getElementById("editGroupId").value = groupId;
  document.getElementById("editGroupName").value = groupName;
  document.getElementById("editModal").style.display = "block";
}

// Закрытие модального окна редактирования
function closeEditModal() {
  document.getElementById("editModal").style.display = "none";
  document.getElementById("editGroupId").value = "";
  document.getElementById("editGroupName").value = "";
}

// Редактирование группы
document.getElementById("editGroupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const groupId = parseInt(document.getElementById("editGroupId").value);
  const name = document.getElementById("editGroupName").value.trim();

  if (!name) {
    showMessage("Введите название группы", "error");
    return;
  }

  try {
    const res = await authFetch(`${API_GROUPS}/${groupId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name: name })
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: await res.text() }));
      throw new Error(errorData.detail || `Ошибка: ${res.status}`);
    }

    const result = await res.json();
    showMessage(`✅ Группа успешно обновлена!`, "success");
    closeEditModal();
    loadGroups();
  } catch (err) {
    showMessage("❌ Ошибка: " + err.message, "error");
  }
});

// Удаление группы
async function deleteGroup(groupId) {
  if (!confirm(`Вы уверены, что хотите удалить группу #${groupId}?`)) {
    return;
  }

  try {
    const res = await authFetch(`${API_GROUPS}/${groupId}`, {
      method: "DELETE"
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: await res.text() }));
      throw new Error(errorData.detail || `Ошибка: ${res.status}`);
    }

    showMessage("✅ Группа успешно удалена!", "success");
    loadGroups();
  } catch (err) {
    showMessage("❌ Ошибка: " + err.message, "error");
  }
}

// Показать сообщение
function showMessage(text, type) {
  const createResult = document.getElementById("createResult");
  createResult.textContent = text;
  createResult.className = `message ${type}`;
  createResult.style.display = "block";

  setTimeout(() => {
    createResult.style.display = "none";
  }, 3000);
}

// Открытие модального окна загрузки файла
function openFileModal(groupId) {
  document.getElementById("fileGroupId").value = groupId;
  document.getElementById("fileLogin").value = "";
  document.getElementById("filePassword").value = "";
  document.getElementById("fileFilename").value = "";
  document.getElementById("fileSkipAuth").checked = false;
  document.getElementById("fileModal").style.display = "block";
}

// Закрытие модального окна загрузки файла
function closeFileModal() {
  document.getElementById("fileModal").style.display = "none";
  document.getElementById("fileGroupId").value = "";
  document.getElementById("fileLogin").value = "";
  document.getElementById("filePassword").value = "";
  document.getElementById("fileFilename").value = "";
  document.getElementById("fileSkipAuth").checked = false;
}

// Обработка загрузки файла
document.getElementById("uploadFileForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const groupId = parseInt(document.getElementById("fileGroupId").value);
  const login = document.getElementById("fileLogin").value.trim();
  const password = document.getElementById("filePassword").value.trim();
  const filename = document.getElementById("fileFilename").value.trim();
  const skipAuth = document.getElementById("fileSkipAuth").checked;

  if (!login || !password) {
    showMessage("Заполните login и password", "error");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("group_id", groupId);
    formData.append("login", login);
    formData.append("password", password);
    if (filename) {
      formData.append("filename", filename);
    }
    if (skipAuth) {
      formData.append("skip_auth", "true");
    }

    const res = await authFetch(`${API_BASE_URL}/admin/files/add`, {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: await res.text() }));
      throw new Error(errorData.detail || `Ошибка: ${res.status}`);
    }

    const result = await res.json();
    showMessage(`✅ Файл успешно загружен для группы!`, "success");
    closeFileModal();
    loadGroups();
  } catch (err) {
    showMessage("❌ Ошибка: " + err.message, "error");
  }
});

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
  const editModal = document.getElementById("editModal");
  const fileModal = document.getElementById("fileModal");
  if (event.target === editModal) {
    closeEditModal();
  }
  if (event.target === fileModal) {
    closeFileModal();
  }
}

