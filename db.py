"""
Модуль для работы с базой данных SQLite.
Инкапсулирует все операции с БД.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
import os


class Database:
    """Класс для работы с базой данных ChatList."""
    
    def __init__(self, db_path: str = "chatlist.db"):
        """
        Инициализация подключения к базе данных.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """Установить соединение с базой данных."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Закрыть соединение с базой данных."""
        if self.conn:
            self.conn.close()
            
    def init_schema(self):
        """Создать все таблицы базы данных."""
        # Читаем SQL схему
        schema_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                self.cursor.executescript(schema_sql)
        else:
            # Если файл не найден, создаём схему напрямую
            self._create_tables_inline()
            
        self.conn.commit()
        
    def _create_tables_inline(self):
        """Создание таблиц встроенным SQL (если init_db.sql не найден)."""
        # Таблица промптов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                prompt_text TEXT NOT NULL,
                tags TEXT
            )
        ''')
        
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date DESC)')
        
        # Таблица моделей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_key_env TEXT NOT NULL,
                model_id TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        ''')
        
        # Таблица результатов
        self.cursor.execute('''
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
            )
        ''')
        
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_date ON results(date DESC)')
        
        # Таблица настроек
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Начальные настройки
        default_settings = [
            ('timeout', '30', 'Таймаут запросов к API в секундах'),
            ('max_retries', '3', 'Максимальное количество повторных попыток'),
            ('theme', 'light', 'Тема интерфейса (light/dark)'),
            ('export_format', 'markdown', 'Формат экспорта по умолчанию')
        ]
        
        for key, value, desc in default_settings:
            self.cursor.execute(
                'INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)',
                (key, value, desc)
            )
        
    # ==================== CRUD для промптов ====================
    
    def add_prompt(self, prompt_text: str, tags: str = None) -> int:
        """Добавить новый промпт."""
        self.cursor.execute(
            'INSERT INTO prompts (prompt_text, tags) VALUES (?, ?)',
            (prompt_text, tags)
        )
        self.conn.commit()
        return self.cursor.lastrowid
        
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Получить все промпты."""
        self.cursor.execute('SELECT * FROM prompts ORDER BY date DESC')
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """Получить промпт по ID."""
        self.cursor.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
        
    def search_prompts(self, query: str) -> List[Dict[str, Any]]:
        """Поиск промптов по тексту или тегам."""
        search_pattern = f'%{query}%'
        self.cursor.execute(
            'SELECT * FROM prompts WHERE prompt_text LIKE ? OR tags LIKE ? ORDER BY date DESC',
            (search_pattern, search_pattern)
        )
        return [dict(row) for row in self.cursor.fetchall()]
        
    def delete_prompt(self, prompt_id: int):
        """Удалить промпт."""
        self.cursor.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
        self.conn.commit()
        
    # ==================== CRUD для моделей ====================
    
    def add_model(self, name: str, api_url: str, api_key_env: str, 
                  model_id: str, is_active: bool = True) -> int:
        """Добавить новую модель."""
        self.cursor.execute(
            '''INSERT INTO models (name, api_url, api_key_env, model_id, is_active) 
               VALUES (?, ?, ?, ?, ?)''',
            (name, api_url, api_key_env, model_id, 1 if is_active else 0)
        )
        self.conn.commit()
        return self.cursor.lastrowid
        
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Получить все модели."""
        self.cursor.execute('SELECT * FROM models ORDER BY name')
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_active_models(self) -> List[Dict[str, Any]]:
        """Получить только активные модели."""
        self.cursor.execute('SELECT * FROM models WHERE is_active = 1 ORDER BY name')
        return [dict(row) for row in self.cursor.fetchall()]
        
    def update_model_status(self, model_id: int, is_active: bool):
        """Изменить статус активности модели."""
        self.cursor.execute(
            'UPDATE models SET is_active = ? WHERE id = ?',
            (1 if is_active else 0, model_id)
        )
        self.conn.commit()
        
    def delete_model(self, model_id: int):
        """Удалить модель."""
        self.cursor.execute('DELETE FROM models WHERE id = ?', (model_id,))
        self.conn.commit()
        
    # ==================== CRUD для результатов ====================
    
    def save_result(self, prompt_id: int, model_id: int, response_text: str,
                   response_time: float = None, tokens_used: int = None) -> int:
        """Сохранить результат запроса."""
        self.cursor.execute(
            '''INSERT INTO results (prompt_id, model_id, response_text, response_time, tokens_used)
               VALUES (?, ?, ?, ?, ?)''',
            (prompt_id, model_id, response_text, response_time, tokens_used)
        )
        self.conn.commit()
        return self.cursor.lastrowid
        
    def get_results_by_prompt(self, prompt_id: int) -> List[Dict[str, Any]]:
        """Получить все результаты для конкретного промпта."""
        self.cursor.execute(
            '''SELECT r.*, m.name as model_name 
               FROM results r
               JOIN models m ON r.model_id = m.id
               WHERE r.prompt_id = ?
               ORDER BY r.date DESC''',
            (prompt_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]
        
    def get_results_by_model(self, model_id: int) -> List[Dict[str, Any]]:
        """Получить все результаты для конкретной модели."""
        self.cursor.execute(
            '''SELECT r.*, p.prompt_text 
               FROM results r
               JOIN prompts p ON r.prompt_id = p.id
               WHERE r.model_id = ?
               ORDER BY r.date DESC''',
            (model_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]
        
    def delete_result(self, result_id: int):
        """Удалить результат."""
        self.cursor.execute('DELETE FROM results WHERE id = ?', (result_id,))
        self.conn.commit()
        
    # ==================== Операции с настройками ====================
    
    def get_setting(self, key: str) -> Optional[str]:
        """Получить значение настройки."""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = self.cursor.fetchone()
        return row['value'] if row else None
        
    def set_setting(self, key: str, value: str):
        """Установить значение настройки."""
        self.cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        self.conn.commit()
        
    def get_all_settings(self) -> Dict[str, str]:
        """Получить все настройки."""
        self.cursor.execute('SELECT key, value FROM settings')
        return {row['key']: row['value'] for row in self.cursor.fetchall()}


if __name__ == '__main__':
    # Тестирование
    db = Database('test.db')
    db.init_schema()
    print("База данных инициализирована успешно!")
    db.close()

