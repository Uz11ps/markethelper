-- БЕЗОПАСНЫЙ скрипт для очистки базы данных
-- Удаляет всех пользователей и группы, но ОСТАВЛЯЕТ ОДНОГО АДМИНА для входа

-- 1. Удаляем связанные данные пользователей
DELETE FROM channel_bonus_requests;
DELETE FROM user_generation_settings;
DELETE FROM pending_bonuses;
DELETE FROM referral_payouts;
DELETE FROM referrals;
DELETE FROM token_purchase_requests;
DELETE FROM requests;
DELETE FROM subscriptions;
DELETE FROM ai_requests;
DELETE FROM product_descriptions;
DELETE FROM editable_prompt_templates;
DELETE FROM infographic_projects;
DELETE FROM mailings;
DELETE FROM broadcast_messages;

-- 2. Удаляем пользователей бота
DELETE FROM users;

-- 3. Удаляем ВСЕХ админов КРОМЕ первого (ID=1)
-- Если у вас админ с другим ID, измените условие
DELETE FROM admins WHERE id != 1;

-- 4. Удаляем группы доступа
DELETE FROM access_groups;

-- 5. Удаляем файлы доступа
DELETE FROM access_files;

-- 6. Удаляем шаблоны дизайна
DELETE FROM design_templates;

-- Настройки (settings) сохранены
-- Системные таблицы (tariffs, statuses, durations, audiences) сохранены

