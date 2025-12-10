// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const API_GROUPS = `${API_BASE_URL}/admin/groups`;

// Загрузка групп при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadGroups();
});

// Загрузка списка групп
async function loadGroups() {
  try {
    const res = await authFetch(API_GROUPS);
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    
    const groups = await res.json();
    renderGroupsTable(groups);
  } catch (err) {
    console.error("Ошибка при загрузке групп:", err);
    const tbody = document.querySelector("#groupsTable tbody");
    tbody.innerHTML = `<tr><td colspan="4">❌ Ошибка при загрузке групп</td></tr>`;
  }
}

// Отрисовка таблицы групп
function renderGroupsTable(groups) {
  const tbody = document.querySelector("#groupsTable tbody");
  tbody.innerHTML = "";

  if (groups.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4">📭 Групп не найдено</td></tr>`;
    return;
  }

  groups.forEach(group => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${group.id}</td>
      <td>${group.name}</td>
      <td>${group.created_at ? new Date(group.created_at).toLocaleDateString() : '—'}</td>
      <td>
        <button onclick="openEditModal(${group.id}, '${group.name}')" class="btn-small btn-primary">✏️ Редактировать</button>
        <button onclick="deleteGroup(${group.id})" class="btn-small btn-danger">🗑️ Удалить</button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// Создание группы
document.getElementById("createGroupForm").addEventListener("submit", async (e) => {
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
    loadGroups();
  } catch (err) {
    showMessage("❌ Ошибка: " + err.message, "error");
  }
});

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

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
  const modal = document.getElementById("editModal");
  if (event.target === modal) {
    closeEditModal();
  }
}

