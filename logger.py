"""
Модуль логирования запросов.
"""

import logging
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir: str = "logs") -> logging.Logger:
    """
    Настроить логгер для приложения.

    Args:
        log_dir: Директория для файлов логов.

    Returns:
        Настроенный логгер.
    """
    # Создать директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Имя файла с датой
    log_file = log_path / f"chatlist_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Настройка логгера
    logger = logging.getLogger("ChatList")
    logger.setLevel(logging.DEBUG)

    # Очистить существующие обработчики
    logger.handlers.clear()

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файловый обработчик
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Глобальный логгер
logger = setup_logger()


def log_request(prompt: str, models: list) -> None:
    """Логировать отправку запроса."""
    model_names = [m.get("name", "Unknown") for m in models]
    logger.info(f"Отправка запроса в {len(models)} моделей: {', '.join(model_names)}")
    logger.debug(f"Промт: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")


def log_response(model_name: str, success: bool, tokens: int = 0, error: str = None) -> None:
    """Логировать ответ от модели."""
    if success:
        logger.info(f"✓ {model_name}: получен ответ ({tokens} токенов)")
    else:
        logger.warning(f"✗ {model_name}: ошибка — {error}")


def log_save_results(count: int) -> None:
    """Логировать сохранение результатов."""
    logger.info(f"Сохранено {count} результатов в базу данных")


def log_export(file_path: str, format_type: str) -> None:
    """Логировать экспорт данных."""
    logger.info(f"Экспорт в {format_type}: {file_path}")


def log_error(message: str, exception: Exception = None) -> None:
    """Логировать ошибку."""
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)


def log_app_start() -> None:
    """Логировать запуск приложения."""
    logger.info("=" * 50)
    logger.info("ChatList запущен")
    logger.info("=" * 50)


def log_app_close() -> None:
    """Логировать закрытие приложения."""
    logger.info("ChatList закрыт")
    logger.info("=" * 50)

