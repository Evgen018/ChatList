"""
Модуль работы с базой данных SQLite.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class Database:
    """Класс для работы с базой данных ChatList."""

    def __init__(self, db_path: str = "chatlist.db"):
        """
        Инициализация подключения к базе данных.

        Args:
            db_path: Путь к файлу базы данных.
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self) -> None:
        """Установить соединение с базой данных."""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def _create_tables(self) -> None:
        """Создать таблицы, если они не существуют."""
        cursor = self.connection.cursor()

        # Таблица промптов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица моделей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'openai',
                api_url TEXT NOT NULL,
                api_key_env TEXT NOT NULL,
                model_id TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица результатов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
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
            )
        """)

        # Таблица настроек
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Индексы
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_prompts_created_at ON prompts(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_is_active ON models(is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_model_id ON results(model_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id)"
        )

        self.connection.commit()

    def close(self) -> None:
        """Закрыть соединение с базой данных."""
        if self.connection:
            self.connection.close()
            self.connection = None

    # === CRUD для промптов ===

    def add_prompt(self, text: str, tags: str = "") -> int:
        """
        Добавить новый промпт.

        Args:
            text: Текст промпта.
            tags: Теги через запятую.

        Returns:
            ID созданного промпта.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO prompts (text, tags) VALUES (?, ?)",
            (text, tags),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_prompts(
        self, search: str = "", limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """
        Получить список промптов.

        Args:
            search: Строка поиска.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список промптов.
        """
        cursor = self.connection.cursor()
        if search:
            cursor.execute(
                """
                SELECT * FROM prompts 
                WHERE text LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (f"%{search}%", f"%{search}%", limit, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM prompts ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        return [dict(row) for row in cursor.fetchall()]

    def get_prompt_by_id(self, prompt_id: int) -> Optional[dict]:
        """Получить промпт по ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_prompt(self, prompt_id: int, text: str, tags: str = "") -> bool:
        """Обновить промпт."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE prompts 
            SET text = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (text, tags, prompt_id),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def delete_prompt(self, prompt_id: int) -> bool:
        """Удалить промпт."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    # === CRUD для моделей ===

    def add_model(
        self,
        name: str,
        provider: str,
        api_url: str,
        api_key_env: str,
        model_id: str,
        is_active: bool = True,
    ) -> int:
        """
        Добавить новую модель.

        Returns:
            ID созданной модели.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO models (name, provider, api_url, api_key_env, model_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, provider, api_url, api_key_env, model_id, int(is_active)),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_models(self, active_only: bool = False) -> list[dict]:
        """
        Получить список моделей.

        Args:
            active_only: Только активные модели.

        Returns:
            Список моделей.
        """
        cursor = self.connection.cursor()
        if active_only:
            cursor.execute(
                "SELECT * FROM models WHERE is_active = 1 ORDER BY name"
            )
        else:
            cursor.execute("SELECT * FROM models ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_model_by_id(self, model_id: int) -> Optional[dict]:
        """Получить модель по ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_model(
        self,
        model_id: int,
        name: str = None,
        provider: str = None,
        api_url: str = None,
        api_key_env: str = None,
        model_id_str: str = None,
        is_active: bool = None,
    ) -> bool:
        """Обновить модель."""
        model = self.get_model_by_id(model_id)
        if not model:
            return False

        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE models 
            SET name = ?, provider = ?, api_url = ?, api_key_env = ?, 
                model_id = ?, is_active = ?
            WHERE id = ?
            """,
            (
                name if name is not None else model["name"],
                provider if provider is not None else model["provider"],
                api_url if api_url is not None else model["api_url"],
                api_key_env if api_key_env is not None else model["api_key_env"],
                model_id_str if model_id_str is not None else model["model_id"],
                int(is_active) if is_active is not None else model["is_active"],
                model_id,
            ),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def toggle_model_active(self, model_id: int) -> bool:
        """Переключить активность модели."""
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE models SET is_active = NOT is_active WHERE id = ?",
            (model_id,),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def delete_model(self, model_id: int) -> bool:
        """Удалить модель."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    # === CRUD для результатов ===

    def save_result(
        self,
        prompt_text: str,
        model_name: str,
        response: str,
        prompt_id: int = None,
        model_id: int = None,
        tokens: int = 0,
    ) -> int:
        """
        Сохранить результат.

        Returns:
            ID созданной записи.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO results 
            (prompt_id, prompt_text, model_id, model_name, response, tokens)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (prompt_id, prompt_text, model_id, model_name, response, tokens),
        )
        self.connection.commit()
        return cursor.lastrowid

    def save_results(self, results: list[dict]) -> list[int]:
        """
        Сохранить несколько результатов.

        Args:
            results: Список словарей с данными результатов.

        Returns:
            Список ID созданных записей.
        """
        ids = []
        for result in results:
            result_id = self.save_result(
                prompt_text=result["prompt_text"],
                model_name=result["model_name"],
                response=result["response"],
                prompt_id=result.get("prompt_id"),
                model_id=result.get("model_id"),
                tokens=result.get("tokens", 0),
            )
            ids.append(result_id)
        return ids

    def get_results(
        self,
        search: str = "",
        model_id: int = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Получить список результатов.

        Args:
            search: Строка поиска.
            model_id: Фильтр по модели.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список результатов.
        """
        cursor = self.connection.cursor()
        query = "SELECT * FROM results WHERE 1=1"
        params = []

        if search:
            query += " AND (prompt_text LIKE ? OR response LIKE ? OR model_name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if model_id:
            query += " AND model_id = ?"
            params.append(model_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_result_by_id(self, result_id: int) -> Optional[dict]:
        """Получить результат по ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_result(self, result_id: int) -> bool:
        """Удалить результат."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    # === CRUD для настроек ===

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """
        Получить значение настройки.

        Args:
            key: Ключ настройки.
            default: Значение по умолчанию.

        Returns:
            Значение настройки или default.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """
        Установить значение настройки.

        Args:
            key: Ключ настройки.
            value: Значение настройки.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        self.connection.commit()

    def get_all_settings(self) -> dict[str, str]:
        """Получить все настройки."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in cursor.fetchall()}

