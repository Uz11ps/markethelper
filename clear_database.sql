-- Скрипт для очистки базы данных от пользователей, админов и групп
-- НАСТРОЙКИ (таблица settings) СОХРАНЯЮТСЯ

-- ВАЖНО: Выполняйте команды в указанном порядке из-за внешних ключей

-- 1. Удаляем связанные данные пользователей (сначала дочерние таблицы)
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

-- 3. Удаляем администраторов (ВНИМАНИЕ: после этого вы не сможете войти в админку!)
-- Если хотите оставить хотя бы одного админа, закомментируйте эту строку
DELETE FROM admins;

-- 4. Удаляем группы доступа
DELETE FROM access_groups;

-- 5. Удаляем файлы доступа
DELETE FROM access_files;

-- 6. Удаляем шаблоны дизайна (если нужно)
DELETE FROM design_templates;

-- Проверка: таблица settings НЕ ТРОГАЕТСЯ - настройки сохранены
-- Проверка: системные таблицы (tariffs, statuses, durations, audiences) НЕ ТРОГАЮТСЯ

