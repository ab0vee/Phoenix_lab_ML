-- ============================================
-- Быстрая настройка БД для разработки
-- ============================================
-- Этот скрипт создает БД, пользователя и применяет схему
-- Используйте для быстрого старта
-- ============================================

-- Создание пользователя (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'phoenix_user') THEN
        CREATE USER phoenix_user WITH PASSWORD 'phoenix_password';
    END IF;
END
$$;

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE phoenix_lab'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'phoenix_lab')\gexec

-- Подключение к базе данных
\c phoenix_lab

-- Выдача прав пользователю
GRANT ALL PRIVILEGES ON DATABASE phoenix_lab TO phoenix_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO phoenix_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO phoenix_user;

-- Применение схемы
\i schema.sql

-- Сообщение об успешном завершении
\echo '✅ База данных phoenix_lab успешно создана и настроена!'
\echo 'Пользователь: phoenix_user'
\echo 'Пароль: phoenix_password (измените в продакшене!)'

