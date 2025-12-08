// Скрипт для обновления URL API в фронтенде для продакшена
// Запустить перед деплоем: node update-frontend-url.js

const fs = require('fs');
const path = require('path');

const PROD_API_URL = 'https://374504.vm.spacecore.network/api';
const FRONTEND_DIR = path.join(__dirname, 'frontend');

const filesToUpdate = [
  'auth.js',
  'settings.js',
  'requests.js',
  'subscription.js',
  'files.js',
  'ai.js'
];

filesToUpdate.forEach(file => {
  const filePath = path.join(FRONTEND_DIR, file);
  
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Заменяем локальный URL на продакшн
    content = content.replace(
      /http:\/\/localhost:8000\/api/g,
      PROD_API_URL
    );
    
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ Обновлен: ${file}`);
  } else {
    console.log(`⚠️  Файл не найден: ${file}`);
  }
});

console.log('✅ Все файлы обновлены для продакшена!');

