# Схема базы данных ChatList

База данных: **SQLite**  
Файл: `chatlist.db`

---

## Таблица `prompts` — Промты

Хранит сохранённые пользователем запросы.

| Поле       | Тип          | Описание                          |
|------------|--------------|-----------------------------------|
| id         | INTEGER      | Первичный ключ, автоинкремент     |
| text       | TEXT         | Текст промта                      |
| tags       | TEXT         | Теги через запятую                |
| created_at | DATETIME     | Дата создания                     |
| updated_at | DATETIME     | Дата последнего изменения         |

```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    tags TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Таблица `models` — Нейросети

Хранит информацию о подключённых нейросетях.

| Поле       | Тип          | Описание                                    |
|------------|--------------|---------------------------------------------|
| id         | INTEGER      | Первичный ключ, автоинкремент               |
| name       | TEXT         | Название модели (GPT-4, Claude и т.д.)      |
| provider   | TEXT         | Провайдер (openai, anthropic, google, etc.) |
| api_url    | TEXT         | URL эндпоинта API                           |
| api_key_env| TEXT         | Имя переменной окружения с API-ключом       |
| model_id   | TEXT         | Идентификатор модели в API                  |
| is_active  | INTEGER      | Активна ли модель (0/1)                     |
| created_at | DATETIME     | Дата добавления                             |

```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'openai',
    api_url TEXT NOT NULL,
    api_key_env TEXT NOT NULL,
    model_id TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Примеры записей:**

| name      | provider  | api_url                              | api_key_env      | model_id          |
|-----------|-----------|--------------------------------------|------------------|-------------------|
| GPT-4o    | openai    | https://api.openai.com/v1/chat       | OPENAI_API_KEY   | gpt-4o            |
| Claude 3  | anthropic | https://api.anthropic.com/v1/messages| ANTHROPIC_API_KEY| claude-3-opus     |
| DeepSeek  | openai    | https://api.deepseek.com/v1/chat     | DEEPSEEK_API_KEY | deepseek-chat     |
| Groq      | openai    | https://api.groq.com/openai/v1/chat  | GROQ_API_KEY     | llama-3.1-70b     |

---

## Таблица `results` — Сохранённые результаты

Хранит выбранные пользователем ответы нейросетей.

| Поле       | Тип          | Описание                          |
|------------|--------------|-----------------------------------|
| id         | INTEGER      | Первичный ключ, автоинкремент     |
| prompt_id  | INTEGER      | Внешний ключ на prompts.id        |
| prompt_text| TEXT         | Текст промта (дублирование)       |
| model_id   | INTEGER      | Внешний ключ на models.id         |
| model_name | TEXT         | Название модели (дублирование)    |
| response   | TEXT         | Текст ответа нейросети            |
| tokens     | INTEGER      | Количество токенов (если доступно)|
| created_at | DATETIME     | Дата сохранения                   |

```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER,
    prompt_text TEXT NOT NULL,
    model_id INTEGER,
    model_name TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
);
```

---

## Таблица `settings` — Настройки

Хранит настройки программы в формате ключ-значение.

| Поле       | Тип          | Описание                          |
|------------|--------------|-----------------------------------|
| id         | INTEGER      | Первичный ключ, автоинкремент     |
| key        | TEXT         | Уникальный ключ настройки         |
| value      | TEXT         | Значение настройки                |
| updated_at | DATETIME     | Дата последнего изменения         |

```sql
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Примеры настроек:**

| key              | value  | Описание                      |
|------------------|--------|-------------------------------|
| request_timeout  | 60     | Таймаут запроса в секундах    |
| max_tokens       | 4096   | Максимум токенов в ответе     |
| theme            | dark   | Тема интерфейса               |
| env_file_path    | .env   | Путь к файлу с API-ключами    |

---

## Диаграмма связей

```
┌─────────────┐       ┌─────────────┐
│   prompts   │       │   models    │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ text        │       │ name        │
│ tags        │       │ provider    │
│ created_at  │       │ api_url     │
│ updated_at  │       │ api_key_env │
└──────┬──────┘       │ model_id    │
       │              │ is_active   │
       │              │ created_at  │
       │              └──────┬──────┘
       │                     │
       │    ┌─────────────┐  │
       └───►│   results   │◄─┘
            ├─────────────┤
            │ id (PK)     │
            │ prompt_id(FK)│
            │ prompt_text │
            │ model_id(FK)│
            │ model_name  │
            │ response    │
            │ tokens      │
            │ created_at  │
            └─────────────┘

┌─────────────┐
│  settings   │
├─────────────┤
│ id (PK)     │
│ key (UNIQUE)│
│ value       │
│ updated_at  │
└─────────────┘
```

---

## Индексы

```sql
-- Для быстрого поиска по промтам
CREATE INDEX idx_prompts_created_at ON prompts(created_at);

-- Для фильтрации активных моделей
CREATE INDEX idx_models_is_active ON models(is_active);

-- Для поиска результатов по дате и модели
CREATE INDEX idx_results_created_at ON results(created_at);
CREATE INDEX idx_results_model_id ON results(model_id);
CREATE INDEX idx_results_prompt_id ON results(prompt_id);
```

