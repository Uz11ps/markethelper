// Конфигурация API (API_BASE_URL уже объявлен в auth.js)
const PRODUCT_API_BASE = `${API_BASE_URL}/product-description`;

class ProductDescriptionManager {
    constructor() {
        this.currentGenerationType = null;
        this.currentProductDescriptionId = null;
        this.currentConcepts = [];
        this.selectedConceptIndex = 0;
        
        this.initEventListeners();
        this.loadProjectsHistory();
    }

    initEventListeners() {
        // Кнопки выбора типа генерации
        document.getElementById('btn-product-only').addEventListener('click', () => {
            this.selectGenerationType('product');
        });
        
        document.getElementById('btn-with-reference').addEventListener('click', () => {
            this.selectGenerationType('reference');
        });

        // Форма загрузки
        document.getElementById('upload-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });

        // Превью изображений
        document.getElementById('product-images').addEventListener('change', (e) => {
            this.handleImagePreview(e.target.files, 'product-preview');
        });
        
        document.getElementById('reference-images').addEventListener('change', (e) => {
            this.handleImagePreview(e.target.files, 'reference-preview');
        });

        // Создание инфографики
        document.getElementById('create-infographic-btn').addEventListener('click', () => {
            this.createInfographic();
        });

        // Кнопки в результатах
        document.getElementById('edit-material-btn').addEventListener('click', () => {
            this.editMaterial();
        });
        
        document.getElementById('edit-prompt-btn').addEventListener('click', () => {
            this.editPrompt();
        });
        
        document.getElementById('download-btn').addEventListener('click', () => {
            this.downloadImage();
        });
        
        document.getElementById('new-generation-btn').addEventListener('click', () => {
            this.resetToStart();
        });
    }

    selectGenerationType(type) {
        this.currentGenerationType = type;
        
        // Обновляем UI
        document.getElementById('generation-type').style.display = 'none';
        document.getElementById('upload-section').style.display = 'block';
        
        if (type === 'reference') {
            document.getElementById('upload-title').textContent = 'Загрузка товара и референса';
            document.getElementById('reference-group').style.display = 'block';
        } else {
            document.getElementById('upload-title').textContent = 'Загрузка фотографий товара';
            document.getElementById('reference-group').style.display = 'none';
        }
    }

    handleImagePreview(files, containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'preview-image';
                img.alt = `Preview ${index + 1}`;
                container.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    }

    async handleFormSubmit() {
        const generateBtn = document.getElementById('generate-btn');
        const generateText = document.getElementById('generate-text');
        const generateLoader = document.getElementById('generate-loader');
        
        generateBtn.disabled = true;
        generateText.style.display = 'none';
        generateLoader.style.display = 'inline-block';

        try {
            const formData = new FormData();
            formData.append('title', document.getElementById('product-title').value);
            formData.append('user_prompt', document.getElementById('user-prompt').value);

            // Добавляем изображения товара
            const productImages = document.getElementById('product-images').files;
            Array.from(productImages).forEach(file => {
                formData.append('product_images', file);
            });

            // Добавляем референсные изображения если есть
            if (this.currentGenerationType === 'reference') {
                const referenceImages = document.getElementById('reference-images').files;
                Array.from(referenceImages).forEach(file => {
                    formData.append('reference_images', file);
                });
            }

            const response = await fetch(`${PRODUCT_API_BASE}/upload-images`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': 'Bearer dummy-token' // TODO: реальная авторизация
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                this.currentProductDescriptionId = result.product_description_id;
                this.currentConcepts = result.concepts;
                this.showConcepts();
            } else {
                throw new Error(result.message || 'Ошибка генерации');
            }

        } catch (error) {
            console.error('Error:', error);
            alert('Ошибка при генерации концепций: ' + error.message);
        } finally {
            generateBtn.disabled = false;
            generateText.style.display = 'inline';
            generateLoader.style.display = 'none';
        }
    }

    showConcepts() {
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';
        
        const conceptsGrid = document.getElementById('concepts-grid');
        conceptsGrid.innerHTML = '';

        this.currentConcepts.forEach((concept, index) => {
            const conceptCard = document.createElement('div');
            conceptCard.className = 'concept-card';
            conceptCard.innerHTML = `
                <h4>${concept.concept_name || `Концепция ${index + 1}`}</h4>
                <p><strong>Описание:</strong> ${concept['🔍 Описание'] || 'Не указано'}</p>
                <p><strong>Фон:</strong> ${concept['🏞️ Фон'] || 'Не указан'}</p>
                <p><strong>Заголовок:</strong> ${concept['🏷️ Заголовок'] || 'Не указан'}</p>
                <div class="concept-offers">
                    <strong>Преимущества:</strong>
                    <ul>
                        ${(concept['💥 Офферы'] || []).map(offer => `<li>${offer}</li>`).join('')}
                    </ul>
                </div>
            `;
            
            conceptCard.addEventListener('click', () => {
                this.selectConcept(index);
            });
            
            conceptsGrid.appendChild(conceptCard);
        });

        // Выбираем первую концепцию по умолчанию
        this.selectConcept(0);
    }

    selectConcept(index) {
        this.selectedConceptIndex = index;
        
        // Обновляем выбранную карточку
        document.querySelectorAll('.concept-card').forEach((card, i) => {
            if (i === index) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });

        // Показываем детали концепции
        const concept = this.currentConcepts[index];
        this.showConceptDetails(concept);
        document.getElementById('concept-details').style.display = 'block';
    }

    showConceptDetails(concept) {
        const conceptInfo = document.getElementById('concept-info');
        conceptInfo.innerHTML = `
            <div class="concept-detail">
                <h4>${concept.concept_name || 'Концепция'}</h4>
                <p><strong>Описание:</strong> ${concept['🔍 Описание'] || 'Не указано'}</p>
                <p><strong>Использование товара:</strong> ${concept['📍 Использование товара'] || 'Не указано'}</p>
                <p><strong>Фон:</strong> ${concept['🏞️ Фон'] || 'Не указан'}</p>
                <p><strong>Заголовок:</strong> ${concept['🏷️ Заголовок'] || 'Не указан'}</p>
                <p><strong>Стиль текста:</strong> ${concept['🖋️ Стиль текста'] || 'Не указан'}</p>
                <p><strong>Стиль иконок:</strong> ${concept['🖌️ Стиль иконок'] || 'Не указан'}</p>
                <p><strong>Расположение иконок:</strong> ${concept['🧩 Расположение иконок'] || 'Не указано'}</p>
                <p><strong>Цветовая палитра:</strong> ${concept.cvetovaya_palitra || 'Не указана'}</p>
            </div>
        `;

        // Заполняем поля редактирования значениями из концепции
        this.updateEditFields(concept);
    }

    updateEditFields(concept) {
        // Обновляем селекты на основе данных концепции
        const iconStyle = document.getElementById('icon-style');
        const iconLayout = document.getElementById('icon-layout');
        const colorPalette = document.getElementById('color-palette');
        const backgroundStyle = document.getElementById('background-style');

        // TODO: Реализовать умное сопоставление значений из концепции с опциями селектов
    }

    async createInfographic() {
        const createBtn = document.getElementById('create-infographic-btn');
        const createText = document.getElementById('create-text');
        const createLoader = document.getElementById('create-loader');
        
        createBtn.disabled = true;
        createText.style.display = 'none';
        createLoader.style.display = 'inline-block';

        try {
            // Сначала создаем проект инфографики
            const projectResponse = await fetch(`${PRODUCT_API_BASE}/infographic-projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer dummy-token'
                },
                body: JSON.stringify({
                    project_type: this.currentGenerationType,
                    title: document.getElementById('product-title').value + ' - Инфографика',
                    product_description_id: this.currentProductDescriptionId,
                    generation_settings: {
                        width: 1080,
                        height: 1080,
                        num_images: 1
                    }
                })
            });

            if (!projectResponse.ok) {
                throw new Error('Ошибка создания проекта');
            }

            const projectResult = await projectResponse.json();
            const projectId = projectResult.project_id;

            // Собираем кастомные редактирования
            const customEdits = {
                icons: {
                    style: document.getElementById('icon-style').value,
                    layout: document.getElementById('icon-layout').value
                },
                colors: {
                    palette: document.getElementById('color-palette').value
                },
                layout: {
                    background: document.getElementById('background-style').value
                }
            };

            // Генерируем инфографику
            const generateResponse = await fetch(`${PRODUCT_API_BASE}/infographic-projects/${projectId}/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer dummy-token'
                },
                body: JSON.stringify({
                    concept_index: this.selectedConceptIndex,
                    custom_prompt_edits: customEdits
                })
            });

            if (!generateResponse.ok) {
                throw new Error('Ошибка генерации инфографики');
            }

            const generateResult = await generateResponse.json();
            this.showFinalResult(generateResult);

        } catch (error) {
            console.error('Error:', error);
            alert('Ошибка при создании инфографики: ' + error.message);
        } finally {
            createBtn.disabled = false;
            createText.style.display = 'inline';
            createLoader.style.display = 'none';
        }
    }

    showFinalResult(result) {
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('final-result').style.display = 'block';
        
        const imageContainer = document.getElementById('final-image-container');
        imageContainer.innerHTML = '';
        
        if (result.generated_images && result.generated_images.length > 0) {
            const img = document.createElement('img');
            img.src = result.generated_images[0];
            img.className = 'final-image';
            img.alt = 'Сгенерированная инфографика';
            imageContainer.appendChild(img);
        }

        const promptContainer = document.getElementById('final-prompt-text');
        promptContainer.innerHTML = `<pre>${result.final_prompt || 'Промт не найден'}</pre>`;
    }

    editMaterial() {
        // Возвращаемся к редактированию концепции
        document.getElementById('final-result').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';
    }

    editPrompt() {
        // Показываем модальное окно для редактирования промта
        const newPrompt = prompt('Редактировать промт:', document.getElementById('final-prompt-text').textContent);
        if (newPrompt) {
            document.getElementById('final-prompt-text').innerHTML = `<pre>${newPrompt}</pre>`;
            // TODO: Сохранить изменения на сервер
        }
    }

    downloadImage() {
        const img = document.querySelector('.final-image');
        if (img) {
            const link = document.createElement('a');
            link.download = 'infographic.png';
            link.href = img.src;
            link.click();
        }
    }

    resetToStart() {
        document.getElementById('final-result').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('generation-type').style.display = 'block';
        
        // Сбрасываем форму
        document.getElementById('upload-form').reset();
        document.getElementById('product-preview').innerHTML = '';
        document.getElementById('reference-preview').innerHTML = '';
        
        this.currentGenerationType = null;
        this.currentProductDescriptionId = null;
        this.currentConcepts = [];
        this.selectedConceptIndex = 0;
    }

    async loadProjectsHistory() {
        try {
            const response = await fetch(`${PRODUCT_API_BASE}/`, {
                headers: {
                    'Authorization': 'Bearer dummy-token'
                }
            });

            if (response.ok) {
                const projects = await response.json();
                this.displayProjectsHistory(projects);
            }
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }

    displayProjectsHistory(projects) {
        const projectsList = document.getElementById('projects-list');
        projectsList.innerHTML = '';

        if (projects.length === 0) {
            projectsList.innerHTML = '<p>Пока нет созданных проектов</p>';
            return;
        }

        projects.forEach(project => {
            const projectCard = document.createElement('div');
            projectCard.className = 'project-card';
            projectCard.innerHTML = `
                <h4>${project.title}</h4>
                <p>Создан: ${new Date(project.created_at).toLocaleDateString()}</p>
                <p>Концепций: ${project.generated_concepts.length}</p>
                <button onclick="productManager.loadProject(${project.id})">Открыть</button>
            `;
            projectsList.appendChild(projectCard);
        });
    }

    async loadProject(projectId) {
        try {
            const response = await fetch(`${PRODUCT_API_BASE}/${projectId}`, {
                headers: {
                    'Authorization': 'Bearer dummy-token'
                }
            });

            if (response.ok) {
                const project = await response.json();
                this.currentProductDescriptionId = project.id;
                this.currentConcepts = project.generated_concepts;
                this.showConcepts();
            }
        } catch (error) {
            console.error('Error loading project:', error);
        }
    }
}

// Инициализация при загрузке страницы
let productManager;
document.addEventListener('DOMContentLoaded', () => {
    productManager = new ProductDescriptionManager();
});
