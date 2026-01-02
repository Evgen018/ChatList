# Схема базы данных ChatList

## Общее описание

База данных SQLite содержит 4 основные таблицы для хранения промптов, моделей нейросетей, результатов запросов и настроек программы.

---

## Таблица: `prompts` (Промпты)

Хранит историю запросов пользователя.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Уникальный идентификатор | PRIMARY KEY, AUTOINCREMENT |
| `date` | DATETIME | Дата и время создания промпта | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `prompt_text` | TEXT | Текст запроса | NOT NULL |
| `tags` | TEXT | Теги (через запятую или JSON) | NULL |

### Индексы:
- `idx_prompts_date` на поле `date` для быстрой сортировки по дате

### SQL создания:
```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt_text TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX idx_prompts_date ON prompts(date DESC);
```

---

## Таблица: `models` (Нейросети)

Хранит информацию о доступных моделях нейросетей.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Уникальный идентификатор | PRIMARY KEY, AUTOINCREMENT |
| `name` | TEXT | Название модели (например, "GPT-4", "DeepSeek") | NOT NULL, UNIQUE |
| `api_url` | TEXT | URL API эндпоинта | NOT NULL |
| `api_key_env` | TEXT | Имя переменной окружения с API-ключом | NOT NULL |
| `model_id` | TEXT | Идентификатор модели в API (например, "gpt-4-turbo") | NOT NULL |
| `is_active` | INTEGER | Активна ли модель (1 = да, 0 = нет) | NOT NULL, DEFAULT 1 |

### SQL создания:
```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_key_env TEXT NOT NULL,
    model_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);
```

### Примеры записей:
```sql
INSERT INTO models (name, api_url, api_key_env, model_id, is_active) VALUES
('GPT-4', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'gpt-4-turbo', 1),
('DeepSeek', 'https://api.deepseek.com/v1/chat/completions', 'DEEPSEEK_API_KEY', 'deepseek-chat', 1),
('Groq Llama', 'https://api.groq.com/v1/chat/completions', 'GROQ_API_KEY', 'llama-3.3-70b-versatile', 0);
```

---

## Таблица: `results` (Результаты)

Хранит сохранённые результаты запросов к нейросетям.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Уникальный идентификатор | PRIMARY KEY, AUTOINCREMENT |
| `prompt_id` | INTEGER | ID промпта из таблицы prompts | FOREIGN KEY, NOT NULL |
| `model_id` | INTEGER | ID модели из таблицы models | FOREIGN KEY, NOT NULL |
| `response_text` | TEXT | Текст ответа от нейросети | NOT NULL |
| `date` | DATETIME | Дата и время получения ответа | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `response_time` | REAL | Время ответа в секундах | NULL |
| `tokens_used` | INTEGER | Количество использованных токенов (если доступно) | NULL |

### Индексы:
- `idx_results_prompt` на поле `prompt_id` для быстрого поиска результатов по промпту
- `idx_results_date` на поле `date` для сортировки по дате

### SQL создания:
```sql
CREATE TABLE results (
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

CREATE INDEX idx_results_prompt ON results(prompt_id);
CREATE INDEX idx_results_date ON results(date DESC);
```

---

## Таблица: `settings` (Настройки)

Хранит настройки программы в формате ключ-значение.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `key` | TEXT | Ключ настройки | PRIMARY KEY |
| `value` | TEXT | Значение настройки | NOT NULL |
| `description` | TEXT | Описание настройки | NULL |

### SQL создания:
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);
```

### Примеры записей:
```sql
INSERT INTO settings (key, value, description) VALUES
('timeout', '30', 'Таймаут запросов к API в секундах'),
('max_retries', '3', 'Максимальное количество повторных попыток'),
('theme', 'light', 'Тема интерфейса (light/dark)'),
('export_format', 'markdown', 'Формат экспорта по умолчанию');
```

---

## Связи между таблицами

```
prompts (1) -----> (*) results
    ↑                   ↑
    |                   |
    └── связь через ──┘
        prompt_id

models (1) -----> (*) results
    ↑                   ↑
    |                   |
    └── связь через ──┘
        model_id
```

### Пояснения:
- Один промпт может иметь много результатов (от разных моделей)
- Одна модель может иметь много результатов (для разных промптов)
- Связь **многие-ко-многим** между `prompts` и `models` реализована через таблицу `results`

---

## Инициализация базы данных

Файл: `init_db.sql`

```sql
-- Создание таблицы промптов
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt_text TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date DESC);

-- Создание таблицы моделей
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_key_env TEXT NOT NULL,
    model_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- Создание таблицы результатов
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

-- Создание таблицы настроек
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- Начальные данные для настроек
INSERT OR IGNORE INTO settings (key, value, description) VALUES
('timeout', '30', 'Таймаут запросов к API в секундах'),
('max_retries', '3', 'Максимальное количество повторных попыток'),
('theme', 'light', 'Тема интерфейса (light/dark)'),
('export_format', 'markdown', 'Формат экспорта по умолчанию');
```

---

## Примечания

1. **Внешние ключи**: включены каскадные удаления для поддержания целостности данных
2. **API-ключи**: хранятся в файле `.env`, в БД только имена переменных
3. **Временная таблица**: результаты до сохранения хранятся в памяти Python, не в БД
4. **Индексы**: созданы для оптимизации частых запросов (сортировка по дате, поиск по промпту)

