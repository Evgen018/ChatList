"""
Конфигурация и константы программы ChatList.
"""

import os

# Версия программы
VERSION = "1.0.0"
APP_NAME = "ChatList"

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "chatlist.db")
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

# Настройки API
API_TIMEOUT = 30  # Таймаут запросов в секундах
MAX_RETRIES = 3   # Максимальное количество повторных попыток

# Настройки интерфейса
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
TABLE_MAX_RESPONSE_LENGTH = 200  # Максимальная длина текста в таблице (для предпросмотра)

# Настройки базы данных
DB_BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# Форматы экспорта
EXPORT_FORMATS = ["markdown", "json", "txt"]

# Темы оформления
THEMES = ["light", "dark"]

# Предустановленные модели (для начальной инициализации)
DEFAULT_MODELS = [
    {
        "name": "GPT-4 Turbo",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "model_id": "gpt-4-turbo-preview",
        "is_active": True
    },
    {
        "name": "GPT-3.5 Turbo",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "model_id": "gpt-3.5-turbo",
        "is_active": True
    },
    {
        "name": "DeepSeek Chat",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_id": "deepseek-chat",
        "is_active": False
    },
    {
        "name": "Groq Llama 3.3 70B",
        "api_url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key_env": "GROQ_API_KEY",
        "model_id": "llama-3.3-70b-versatile",
        "is_active": False
    },
    {
        "name": "Claude 3.5 Sonnet",
        "api_url": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "model_id": "claude-3-5-sonnet-20241022",
        "is_active": False
    }
]

# Стили для интерфейса (будут использоваться в main.py)
LIGHT_THEME_STYLE = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    QTableWidget {
        background-color: white;
        alternate-background-color: #f9f9f9;
    }
"""

DARK_THEME_STYLE = """
    QMainWindow {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QTableWidget {
        background-color: #3c3c3c;
        alternate-background-color: #444444;
        color: #ffffff;
    }
"""


def create_backup_dir():
    """Создать директорию для бэкапов, если её нет."""
    if not os.path.exists(DB_BACKUP_DIR):
        os.makedirs(DB_BACKUP_DIR)


def get_config_value(key: str, default=None):
    """
    Получить значение конфигурации из переменных окружения или использовать дефолт.
    
    Args:
        key: Ключ конфигурации
        default: Значение по умолчанию
        
    Returns:
        Значение конфигурации
    """
    return os.getenv(key, default)


if __name__ == '__main__':
    print(f"{APP_NAME} v{VERSION}")
    print(f"База данных: {DATABASE_PATH}")
    print(f"Таймаут API: {API_TIMEOUT}с")
    print(f"Максимум попыток: {MAX_RETRIES}")

