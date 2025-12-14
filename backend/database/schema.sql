-- ============================================
-- Схема базы данных Phoenix LAB
-- ============================================
-- Этот файл содержит SQL скрипты для создания всех таблиц
-- Используется для первоначальной настройки БД
-- ============================================

-- Создание базы данных (выполняется отдельно, если нужно)
-- CREATE DATABASE phoenix_lab;
-- \c phoenix_lab;

-- ============================================
-- Таблица пользователей
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Индекс для быстрого поиска по username
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- Таблица ссылок пользователей
-- ============================================
CREATE TABLE IF NOT EXISTS user_urls (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, archived, deleted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_processed_at TIMESTAMP,
    metadata JSONB, -- Дополнительные данные (результаты обработки, теги и т.д.)
    
    -- Уникальность: один пользователь не может добавить одну ссылку дважды
    CONSTRAINT unique_user_url UNIQUE (user_id, url)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_user_urls_user_id ON user_urls(user_id);
CREATE INDEX IF NOT EXISTS idx_user_urls_status ON user_urls(status);
CREATE INDEX IF NOT EXISTS idx_user_urls_created_at ON user_urls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_urls_url ON user_urls USING gin(to_tsvector('russian', url));

-- ============================================
-- Таблица результатов обработки ссылок
-- ============================================
CREATE TABLE IF NOT EXISTS url_processing_results (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES user_urls(id) ON DELETE CASCADE,
    original_text TEXT,
    summarized_text TEXT,
    paraphrased_text TEXT,
    language VARCHAR(10), -- ru, en
    processing_time FLOAT, -- время обработки в секундах
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB -- дополнительные данные обработки
);

CREATE INDEX IF NOT EXISTS idx_processing_results_url_id ON url_processing_results(url_id);
CREATE INDEX IF NOT EXISTS idx_processing_results_created_at ON url_processing_results(created_at DESC);

-- ============================================
-- Таблица сессий пользователей (опционально)
-- ============================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- ============================================
-- Функция для автоматического обновления updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_urls_updated_at BEFORE UPDATE ON user_urls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Комментарии к таблицам (для документации)
-- ============================================
COMMENT ON TABLE users IS 'Пользователи системы';
COMMENT ON TABLE user_urls IS 'Ссылки, добавленные пользователями';
COMMENT ON TABLE url_processing_results IS 'Результаты обработки ссылок (суммаризация, парафразирование)';
COMMENT ON TABLE user_sessions IS 'Сессии пользователей для аутентификации';

COMMENT ON COLUMN users.password_hash IS 'Хеш пароля (bcrypt, argon2 и т.д.)';
COMMENT ON COLUMN user_urls.metadata IS 'JSON с дополнительными данными: теги, категории, результаты обработки';
COMMENT ON COLUMN url_processing_results.metadata IS 'JSON с метаданными обработки: модель, параметры, статистика';

