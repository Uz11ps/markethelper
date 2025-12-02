const API_ROOT = `${window.location.protocol}//${window.location.hostname}:8000`;
const DESIGN_API = `${API_ROOT}/designs`;
const AI_API = `${API_ROOT}/ai`;

const state = {
  mode: "infographic",
  infographic: {
    referenceBase64: null,
    templateId: null,
  },
  custom: {
    referenceBase64: null,
  },
  competitor: {
    competitorBase64: null,
    productBase64: null,
    storedTemplateId: null,
    previewUrl: null,
  },
};

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });
  document.querySelectorAll(".mode-panel").forEach((panel) => {
    panel.classList.toggle("hidden", panel.id !== `panel-${mode}`);
  });
}

async function fileToBase64(file) {
  if (!file) return null;
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Не удалось прочитать файл"));
    reader.readAsDataURL(file);
  });
}

function showWarnings(container, warnings) {
  if (!container) return;
  if (!warnings || !warnings.length) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }
  container.classList.remove("hidden");
  container.innerHTML = warnings
    .map((warn) => `<div>⚠️ ${warn}</div>`)
    .join("");
}

function extractImageUrls(data) {
  const urls = new Set();
  if (!data) {
    return Array.from(urls);
  }

  const collect = (value) => {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(collect);
      return;
    }
    if (typeof value === "object") {
      const directUrl = value.url || value.image_url || value.secure_url;
      if (typeof directUrl === "string" && directUrl.startsWith("http")) {
        urls.add(directUrl);
      }
      Object.values(value).forEach(collect);
      return;
    }
    if (typeof value === "string" && value.startsWith("http")) {
      urls.add(value);
    }
  };

  collect(data);
  return Array.from(urls);
}

function renderGenerationResult(container, payload) {
  if (!container) return;
  container.innerHTML = "";
  if (!payload) {
    container.innerHTML = `<div class="empty-info">Нет данных от сервиса генерации</div>`;
    return;
  }

  const urls = extractImageUrls(payload);
  if (urls.length) {
    const gallery = document.createElement("div");
    gallery.className = "result-gallery";
    urls.forEach((url) => {
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      const img = document.createElement("img");
      img.src = url;
      img.alt = "Результат генерации";
      link.appendChild(img);
      gallery.appendChild(link);
    });
    container.appendChild(gallery);
  }

  const details = document.createElement("pre");
  details.className = "result-json";
  details.textContent = JSON.stringify(payload, null, 2);
  container.appendChild(details);
}

async function requestPrompt(body) {
  const res = await fetch(`${DESIGN_API}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = data?.detail || "Не удалось получить промт";
    throw new Error(detail);
  }
  return res.json();
}

async function requestImageGeneration(body) {
  const res = await fetch(`${AI_API}/images/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data?.detail || "Ошибка генерации изображения";
    throw new Error(detail);
  }
  return data;
}

function bindModeSwitcher() {
  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });
}

function setupInfographicFlow() {
  const form = document.getElementById("infographicPromptForm");
  const promptBlock = document.getElementById("infographicPromptResult");
  const promptText = document.getElementById("infographicPromptText");
  const negText = document.getElementById("infographicNegativeText");
  const warningsBox = document.getElementById("infographicWarnings");
  const templateInfo = document.getElementById("infographicTemplateInfo");
  const resultContainer = document.getElementById("infographicGenerationResult");
  const generateBtn = document.getElementById("infographicGenerateBtn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = document.getElementById("infographicReference").files[0];
    if (!file) {
      alert("Пожалуйста, добавьте изображение-референс.");
      return;
    }
    try {
      form.querySelector("button[type='submit']").disabled = true;
      form.querySelector("button[type='submit']").textContent = "Обработка...";

      const referenceBase64 = await fileToBase64(file);
      state.infographic.referenceBase64 = referenceBase64;

      const body = {
        mode: "infographic",
        reference_image_base64: referenceBase64,
        template_type: document.getElementById("infographicType").value,
        product_keywords: document.getElementById("infographicKeywords").value || null,
      };

      const response = await requestPrompt(body);
      promptText.value = response.prompt || "";
      negText.value = response.negative_prompt || "";
      state.infographic.templateId = response.template_id || null;
      promptBlock.classList.remove("hidden");
      showWarnings(warningsBox, response.warnings);

      if (response.template_name) {
        templateInfo.textContent = `Использован шаблон: ${response.template_name}`;
      } else {
        templateInfo.textContent = "Подготовлен промт на основе вашего референса.";
      }
      resultContainer.innerHTML = "";
    } catch (err) {
      alert(err.message);
    } finally {
      const submitBtn = form.querySelector("button[type='submit']");
      submitBtn.disabled = false;
      submitBtn.textContent = "Получить промт";
    }
  });

  generateBtn.addEventListener("click", async () => {
    if (!state.infographic.referenceBase64) {
      alert("Сначала загрузите изображение и получите промт.");
      return;
    }
    const prompt = promptText.value.trim();
    if (prompt.length < 5) {
      alert("Промт слишком короткий.");
      return;
    }

    try {
      generateBtn.disabled = true;
      generateBtn.textContent = "Генерация...";

      const payload = {
        prompt,
        reference_image_base64: state.infographic.referenceBase64,
      };
      const negative = negText.value.trim();
      if (negative) payload.negative_prompt = negative;

      const res = await requestImageGeneration(payload);
      renderGenerationResult(resultContainer, res.data || res);
    } catch (err) {
      alert(err.message);
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = "Начать генерацию";
    }
  });
}

function setupCustomFlow() {
  const form = document.getElementById("customPromptForm");
  const promptBlock = document.getElementById("customPromptResult");
  const warningsBox = document.getElementById("customWarnings");
  const initialPrompt = document.getElementById("customPromptText");
  const initialNegative = document.getElementById("customNegativeText");
  const finalPrompt = document.getElementById("customPromptFinal");
  const finalNegative = document.getElementById("customNegativeFinal");
  const generateBtn = document.getElementById("customGenerateBtn");
  const resultContainer = document.getElementById("customGenerationResult");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const promptValue = initialPrompt.value.trim();
    if (promptValue.length < 5) {
      alert("Пожалуйста, опишите желаемый результат подробнее.");
      return;
    }

    const file = document.getElementById("customReference").files[0];
    if (file) {
      try {
        state.custom.referenceBase64 = await fileToBase64(file);
      } catch (err) {
        alert(err.message);
        return;
      }
    } else {
      state.custom.referenceBase64 = null;
    }

    try {
      const body = {
        mode: "custom",
        prompt: promptValue,
        negative_prompt: initialNegative.value || null,
      };
      form.querySelector("button[type='submit']").disabled = true;
      form.querySelector("button[type='submit']").textContent = "Проверка...";
      const response = await requestPrompt(body);
      finalPrompt.value = response.prompt || promptValue;
      finalNegative.value = response.negative_prompt || initialNegative.value;
      promptBlock.classList.remove("hidden");
      showWarnings(warningsBox, response.warnings);
      resultContainer.innerHTML = "";
    } catch (err) {
      alert(err.message);
    } finally {
      const submitBtn = form.querySelector("button[type='submit']");
      submitBtn.disabled = false;
      submitBtn.textContent = "Проверить промт";
    }
  });

  generateBtn.addEventListener("click", async () => {
    const prompt = finalPrompt.value.trim();
    if (prompt.length < 5) {
      alert("Промт слишком короткий.");
      return;
    }

    const payload = { prompt };
    const negative = finalNegative.value.trim();
    if (negative) payload.negative_prompt = negative;
    if (state.custom.referenceBase64) {
      payload.reference_image_base64 = state.custom.referenceBase64;
    }

    try {
      generateBtn.disabled = true;
      generateBtn.textContent = "Генерация...";
      const res = await requestImageGeneration(payload);
      renderGenerationResult(resultContainer, res.data || res);
    } catch (err) {
      alert(err.message);
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = "Начать генерацию";
    }
  });
}

function setupCompetitorFlow() {
  const form = document.getElementById("competitorPromptForm");
  const promptBlock = document.getElementById("competitorPromptResult");
  const promptText = document.getElementById("competitorPromptText");
  const negativeText = document.getElementById("competitorNegativeText");
  const warningsBox = document.getElementById("competitorWarnings");
  const templateInfo = document.getElementById("competitorTemplateInfo");
  const productReferenceInput = document.getElementById("competitorProductReference");
  const resultContainer = document.getElementById("competitorGenerationResult");
  const generateBtn = document.getElementById("competitorGenerateBtn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = document.getElementById("competitorReference").files[0];
    if (!file) {
      alert("Добавьте слайд конкурента.");
      return;
    }

    try {
      const submitBtn = form.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Обработка...";

      const referenceBase64 = await fileToBase64(file);
      state.competitor.competitorBase64 = referenceBase64;
      state.competitor.productBase64 = null;

      const body = {
        mode: "competitor",
        reference_image_base64: referenceBase64,
        product_name: document.getElementById("competitorProductName").value || "nano banana",
        template_type: document.getElementById("competitorType").value,
        product_keywords: document.getElementById("competitorKeywords").value || null,
      };

      const response = await requestPrompt(body);
      promptText.value = response.prompt || "";
      negativeText.value = response.negative_prompt || "";
      promptBlock.classList.remove("hidden");
      showWarnings(warningsBox, response.warnings);
      state.competitor.storedTemplateId = response.stored_template_id || null;
      state.competitor.previewUrl = response.preview_url || null;
      resultContainer.innerHTML = "";

      const templateIdLabel = response.stored_template_id
        ? `Сохранено в библиотеку (ID: ${response.stored_template_id})`
        : "Промт подготовлен.";
      templateInfo.textContent = templateIdLabel;

      productReferenceInput.value = "";
    } catch (err) {
      alert(err.message);
    } finally {
      const submitBtn = form.querySelector("button[type='submit']");
      submitBtn.disabled = false;
      submitBtn.textContent = "Получить промт";
    }
  });

  productReferenceInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) {
      state.competitor.productBase64 = null;
      return;
    }
    try {
      state.competitor.productBase64 = await fileToBase64(file);
    } catch (err) {
      alert(err.message);
      state.competitor.productBase64 = null;
      event.target.value = "";
    }
  });

  generateBtn.addEventListener("click", async () => {
    if (!state.competitor.competitorBase64) {
      alert("Сначала загрузите слайд конкурента и получите промт.");
      return;
    }
    if (!state.competitor.productBase64) {
      alert("Добавьте фото вашего товара для генерации.");
      return;
    }
    const prompt = promptText.value.trim();
    if (prompt.length < 5) {
      alert("Промт слишком короткий.");
      return;
    }

    const payload = {
      prompt,
      reference_image_base64: state.competitor.productBase64,
    };
    const negative = negativeText.value.trim();
    if (negative) payload.negative_prompt = negative;

    try {
      generateBtn.disabled = true;
      generateBtn.textContent = "Генерация...";
      const res = await requestImageGeneration(payload);
      renderGenerationResult(resultContainer, res.data || res);
    } catch (err) {
      alert(err.message);
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = "Начать генерацию";
    }
  });
}

function init() {
  bindModeSwitcher();
  setupInfographicFlow();
  setupCustomFlow();
  setupCompetitorFlow();
}

document.addEventListener("DOMContentLoaded", init);
