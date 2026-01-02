-- Инициализация базы данных ChatList
-- Этот файл создаёт все необходимые таблицы и начальные данные

-- ==================== Таблица промптов ====================
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt_text TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date DESC);

-- ==================== Таблица моделей ====================
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_key_env TEXT NOT NULL,
    model_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- ==================== Таблица результатов ====================
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_time REAL,
    tokens_used INTEGER,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_date ON results(date DESC);

-- ==================== Таблица настроек ====================
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- ==================== Начальные данные ====================

-- Настройки по умолчанию
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('timeout', '30', 'Таймаут запросов к API в секундах'),
    ('max_retries', '3', 'Максимальное количество повторных попыток'),
    ('theme', 'light', 'Тема интерфейса (light/dark)'),
    ('export_format', 'markdown', 'Формат экспорта по умолчанию');

-- Предустановленные модели
INSERT OR IGNORE INTO models (name, api_url, api_key_env, model_id, is_active) VALUES
    ('GPT-4 Turbo', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'gpt-4-turbo-preview', 1),
    ('GPT-3.5 Turbo', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'gpt-3.5-turbo', 1),
    ('DeepSeek Chat', 'https://api.deepseek.com/v1/chat/completions', 'DEEPSEEK_API_KEY', 'deepseek-chat', 0),
    ('Groq Llama 3.3 70B', 'https://api.groq.com/openai/v1/chat/completions', 'GROQ_API_KEY', 'llama-3.3-70b-versatile', 0),
    ('Claude 3.5 Sonnet', 'https://api.anthropic.com/v1/messages', 'ANTHROPIC_API_KEY', 'claude-3-5-sonnet-20241022', 0);

