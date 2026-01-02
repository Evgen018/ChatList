"""
Вспомогательные функции для программы ChatList.
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any
from config import DB_BACKUP_DIR, TABLE_MAX_RESPONSE_LENGTH


def truncate_text(text: str, max_length: int = TABLE_MAX_RESPONSE_LENGTH) -> str:
    """
    Обрезать текст до указанной длины.
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        
    Returns:
        Обрезанный текст с многоточием
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
        
    return text[:max_length] + "..."


def format_datetime(dt_string: str, format_string: str = "%d.%m.%Y %H:%M") -> str:
    """
    Форматировать строку даты/времени.
    
    Args:
        dt_string: Строка с датой/временем из БД
        format_string: Формат вывода
        
    Returns:
        Отформатированная строка
    """
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime(format_string)
    except:
        return dt_string


def format_response_time(seconds: float) -> str:
    """
    Форматировать время ответа.
    
    Args:
        seconds: Время в секундах
        
    Returns:
        Строка вида "1.23с"
    """
    if seconds is None:
        return "—"
    return f"{seconds:.2f}с"


def format_tokens(tokens: int) -> str:
    """
    Форматировать количество токенов.
    
    Args:
        tokens: Количество токенов
        
    Returns:
        Строка с форматированным числом
    """
    if tokens is None:
        return "—"
    return f"{tokens:,}".replace(",", " ")


def export_to_markdown(results: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Экспортировать результаты в Markdown файл.
    
    Args:
        results: Список результатов
        filepath: Путь к файлу
        
    Returns:
        True если успешно, False иначе
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Результаты ChatList\n\n")
            f.write(f"Экспортировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
            f.write("---\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"## {i}. {result.get('model_name', 'Неизвестная модель')}\n\n")
                f.write(f"**Время ответа:** {format_response_time(result.get('response_time'))}\n\n")
                f.write(f"**Токенов:** {format_tokens(result.get('tokens_used'))}\n\n")
                f.write(f"**Ответ:**\n\n{result.get('response_text', '')}\n\n")
                f.write("---\n\n")
                
        return True
    except Exception as e:
        print(f"Ошибка экспорта в Markdown: {e}")
        return False


def export_to_json(results: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Экспортировать результаты в JSON файл.
    
    Args:
        results: Список результатов
        filepath: Путь к файлу
        
    Returns:
        True если успешно, False иначе
    """
    try:
        export_data = {
            "export_date": datetime.now().isoformat(),
            "results": results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        print(f"Ошибка экспорта в JSON: {e}")
        return False


def export_to_txt(results: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Экспортировать результаты в текстовый файл.
    
    Args:
        results: Список результатов
        filepath: Путь к файлу
        
    Returns:
        True если успешно, False иначе
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("РЕЗУЛЬТАТЫ CHATLIST\n")
            f.write(f"Экспортировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result.get('model_name', 'Неизвестная модель')}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Время ответа: {format_response_time(result.get('response_time'))}\n")
                f.write(f"Токенов: {format_tokens(result.get('tokens_used'))}\n\n")
                f.write(f"{result.get('response_text', '')}\n\n")
                f.write("=" * 80 + "\n\n")
                
        return True
    except Exception as e:
        print(f"Ошибка экспорта в TXT: {e}")
        return False


def backup_database(db_path: str) -> bool:
    """
    Создать резервную копию базы данных.
    
    Args:
        db_path: Путь к файлу БД
        
    Returns:
        True если успешно, False иначе
    """
    try:
        if not os.path.exists(db_path):
            return False
            
        # Создаём директорию для бэкапов
        if not os.path.exists(DB_BACKUP_DIR):
            os.makedirs(DB_BACKUP_DIR)
            
        # Имя файла с текущей датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"chatlist_backup_{timestamp}.db"
        backup_path = os.path.join(DB_BACKUP_DIR, backup_filename)
        
        # Копируем файл
        shutil.copy2(db_path, backup_path)
        
        print(f"Бэкап создан: {backup_path}")
        return True
        
    except Exception as e:
        print(f"Ошибка создания бэкапа: {e}")
        return False


def validate_api_key(api_key: str) -> bool:
    """
    Проверить валидность API ключа (базовая проверка).
    
    Args:
        api_key: API ключ
        
    Returns:
        True если ключ выглядит валидным
    """
    if not api_key:
        return False
        
    # Базовая проверка: длина и отсутствие пробелов
    return len(api_key) > 10 and ' ' not in api_key


def parse_tags(tags_string: str) -> List[str]:
    """
    Разобрать строку тегов в список.
    
    Args:
        tags_string: Строка с тегами через запятую
        
    Returns:
        Список тегов
    """
    if not tags_string:
        return []
        
    return [tag.strip() for tag in tags_string.split(',') if tag.strip()]


def tags_to_string(tags_list: List[str]) -> str:
    """
    Преобразовать список тегов в строку.
    
    Args:
        tags_list: Список тегов
        
    Returns:
        Строка с тегами через запятую
    """
    if not tags_list:
        return ""
        
    return ", ".join(tags_list)


if __name__ == '__main__':
    # Тесты
    print("Тест truncate_text:", truncate_text("A" * 300, 50))
    print("Тест format_response_time:", format_response_time(1.2345))
    print("Тест format_tokens:", format_tokens(12345))
    print("Тест parse_tags:", parse_tags("python, api, openai"))
    print("Модуль utils.py готов к использованию")

