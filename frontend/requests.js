const API_BASE = "http://31.97.183.139:8000/admin/requests";

async function loadRequests() {
  try {
    const res = await fetch(API_BASE + "/");
    if (!res.ok) {
      throw new Error(`Ошибка запроса: ${res.status}`);
    }

    const data = await res.json();

    const tbody = document.querySelector("#requestsTable tbody");
    tbody.innerHTML = "";

    // Фильтруем только новые заявки
    const pending = data.filter(req => req.status === "В ожидании");

    if (pending.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">Новых заявок нет</td></tr>`;
      return;
    }

    pending.forEach(req => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${req.id}</td>
        <td>
          ${req.username 
            ? `<a href="https://t.me/${req.username}" target="_blank">@${req.username}</a>` 
            : `<span style="color: gray;">нет username</span>`}
        </td>
        <td>${req.tariff_code}</td>
        <td>${req.duration_months} мес.</td>
        <td>${req.status}</td>
        <td>${new Date(req.created_at).toLocaleDateString()}</td>
        <td>
          <input type="text" id="filename-${req.id}" placeholder="Имя файла" />
          <button class="approve" onclick="approve(${req.id})">Принять</button>
          <button class="reject" onclick="reject(${req.id})">Отклонить</button>
        </td>
      `;

      tbody.appendChild(row);
    });


  } catch (err) {
    console.error("Ошибка при загрузке заявок:", err);
    const tbody = document.querySelector("#requestsTable tbody");
    tbody.innerHTML = `<tr><td colspan="7">Ошибка при загрузке заявок</td></tr>`;
  }
}
async function approve(id) {
  try {
    const input = document.querySelector(`#filename-${id}`);
    const filename = input.value.trim();
    const formData = new FormData();
    formData.append("filename", filename);

    const res = await fetch(`${API_BASE}/${id}/approve`, {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    loadRequests();
  } catch (err) {
    console.error(err);
    alert("Не удалось принять заявку");
  }
}
async function reject(id) {
  try {
    const res = await fetch(`${API_BASE}/${id}/reject`, { method: "POST" });
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    loadRequests();
  } catch (err) {
    console.error(err);
    alert("Не удалось отклонить заявку");
  }
}

loadRequests();
