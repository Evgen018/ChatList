# ChatList

Python-приложение для отправки промптов в несколько нейросетей и сравнения их ответов.

## 📋 Описание

ChatList позволяет:
- Отправлять один промпт одновременно в несколько AI моделей (GPT-4, DeepSeek, Groq, Claude и др.)
- Сравнивать ответы разных моделей в удобной таблице
- Сохранять выбранные результаты в базу данных
- Экспортировать результаты в Markdown, JSON или TXT
- Управлять списком моделей и их настройками

## 🚀 Быстрый старт

### 1. Установка зависимостей

```powershell
pip install -r requirements.txt
```

### 2. Настройка API-ключей

Скопируйте файл с примерами:
```powershell
Copy-Item .env.example .env
```

Откройте `.env` и добавьте свои API-ключи:
```env
OPENAI_API_KEY=sk-proj-ваш_ключ_здесь
DEEPSEEK_API_KEY=ваш_ключ_здесь
GROQ_API_KEY=ваш_ключ_здесь
ANTHROPIC_API_KEY=ваш_ключ_здесь
```

### 3. Инициализация базы данных

```powershell
python -c "from db import Database; db = Database(); db.init_schema(); print('БД инициализирована'); db.close()"
```

### 4. Запуск приложения

```powershell
python main.py
```

## 📦 Создание исполняемого файла

Для создания standalone .exe файла:

```powershell
.\build.ps1
```

Исполняемый файл будет создан в папке `dist\ChatListApp.exe`

## 🏗️ Структура проекта

```
ChatList/
├── main.py          # Главный файл с GUI (PyQt5)
├── db.py            # Работа с базой данных SQLite
├── models.py        # Классы Model, Result, PromptRequest
├── network.py       # Отправка запросов к API
├── config.py        # Конфигурация и константы
├── utils.py         # Вспомогательные функции
├── init_db.sql      # SQL схема базы данных
├── requirements.txt # Зависимости Python
├── .env.example     # Примеры API-ключей
├── DATABASE.md      # Описание схемы БД
├── PLAN.md          # План разработки
└── PROJECT.md       # Спецификация проекта
```

## 🔑 Получение API-ключей

- **OpenAI (GPT-4, GPT-3.5)**: https://platform.openai.com/api-keys
- **DeepSeek**: https://platform.deepseek.com/api-keys
- **Groq (Llama, Mixtral)**: https://console.groq.com/keys
- **Anthropic (Claude)**: https://console.anthropic.com/settings/keys

## 📚 Документация

- [DATABASE.md](DATABASE.md) - Подробная схема базы данных
- [PLAN.md](PLAN.md) - Поэтапный план разработки
- [PROJECT.md](PROJECT.md) - Полная спецификация проекта

## 🛠️ Технологии

- **Python 3.11+**
- **PyQt5** - графический интерфейс
- **SQLite** - база данных
- **requests** - HTTP запросы к API
- **python-dotenv** - управление переменными окружения

## ⚙️ Требования

- Python 3.11 или выше
- Windows 10/11 (для .exe файла)
- API-ключи хотя бы для одной нейросети

## 📝 Лицензия

См. файл [LICENSE](LICENSE)

## 🤝 Разработка

Проект готов к использованию! Текущий статус:
- ✅ Этап 1: Подготовка проекта
- ✅ Этап 2: База данных
- ✅ Этап 3: Работа с API
- ✅ Этап 4: Логика моделей
- ✅ Этап 5: Графический интерфейс
- 🟡 Этап 6-9: Дополнительные улучшения (опционально)

**Версия: 1.0.0 - Готово к использованию!**

Подробный план см. в [PLAN.md](PLAN.md)  
Руководство пользователя: [USER_GUIDE.md](USER_GUIDE.md)
