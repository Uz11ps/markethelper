const API_BASE = "http://31.97.183.139:8000/ai";

// Проверка здоровья
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Ошибка запроса: ${res.status}`);
    const data = await res.json();
    document.getElementById("healthStatus").innerText =
      data.status === "ok" ? "✅ AI работает" : "❌ Не доступен";
  } catch (err) {
    console.error("Ошибка при проверке здоровья:", err);
    document.getElementById("healthStatus").innerText = "⚠️ Ошибка проверки";
  }
}

// Загрузка текста или PDF
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  try {
    const formData = new FormData(e.target);
    const res = await fetch(`${API_BASE}/texts`, {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    const data = await res.json();

    document.getElementById("uploadResult").innerText = JSON.stringify(data, null, 2);
    loadTexts();
  } catch (err) {
    console.error("Ошибка при загрузке текста/PDF:", err);
    document.getElementById("uploadResult").innerText = "⚠️ Ошибка загрузки";
  }
});

// Загрузка всех текстов
async function loadTexts() {
  try {
    const res = await fetch(`${API_BASE}/texts`);
    if (!res.ok) throw new Error(`Ошибка запроса: ${res.status}`);
    const data = await res.json();

    const tbody = document.querySelector("#textsTable tbody");
    tbody.innerHTML = "";

    if (!data || data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5">Нет сохранённых текстов</td></tr>`;
      return;
    }

    data.forEach((item) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${item.id || "-"}</td>
        <td>${item.metadata?.source || "-"}</td>
        <td>${item.metadata?.type || "-"}</td>
        <td>${item.text?.slice(0, 100) || "-"}</td>
        <td><button onclick="deleteText('${item.id}')">🗑 Удалить</button></td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Ошибка при загрузке текстов:", err);
    const tbody = document.querySelector("#textsTable tbody");
    tbody.innerHTML = `<tr><td colspan="5">⚠️ Ошибка загрузки</td></tr>`;
  }
}

// Удаление текста
async function deleteText(id) {
  if (!confirm("Удалить этот текст?")) return;
  try {
    const res = await fetch(`${API_BASE}/texts/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    loadTexts();
  } catch (err) {
    console.error("Ошибка при удалении:", err);
    alert("Не удалось удалить текст");
  }
}

// Отправка вопроса к AI
document.getElementById("queryForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = document.getElementById("question").value;

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    if (!res.ok) throw new Error(`Ошибка: ${res.status}`);
    const data = await res.json();

    document.getElementById("answerBox").innerHTML =
      `<b>Ответ:</b> ${data.answer}<br><small>⏱ ${data.time_seconds.toFixed(2)} сек</small>`;
  } catch (err) {
    console.error("Ошибка при запросе AI:", err);
    document.getElementById("answerBox").innerText = "⚠️ Ошибка при запросе";
  }
});

// При загрузке страницы подтянем тексты
loadTexts();
checkHealth();
