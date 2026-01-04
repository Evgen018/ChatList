"""
Модуль логики работы с моделями.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from db import Database
from network import get_client


@dataclass
class TempResult:
    """Временный результат запроса (хранится в памяти)."""

    model_id: int
    model_name: str
    prompt_text: str
    response: str
    tokens: int = 0
    selected: bool = False
    success: bool = True
    error: Optional[str] = None


class ResultsStore:
    """Временное хранилище результатов в памяти."""

    def __init__(self):
        """Инициализация хранилища."""
        self._results: list[TempResult] = []
        self._current_prompt: str = ""

    @property
    def results(self) -> list[TempResult]:
        """Получить все результаты."""
        return self._results

    @property
    def current_prompt(self) -> str:
        """Получить текущий промт."""
        return self._current_prompt

    def set_results(self, prompt: str, results: list[dict]) -> None:
        """
        Установить новые результаты.

        Args:
            prompt: Текст промта.
            results: Список результатов от API.
        """
        self.clear()
        self._current_prompt = prompt

        for result in results:
            self._results.append(
                TempResult(
                    model_id=result.get("model_id", 0),
                    model_name=result.get("model_name", ""),
                    prompt_text=result.get("prompt_text", prompt),
                    response=result.get("response", ""),
                    tokens=result.get("tokens", 0),
                    selected=False,
                    success=result.get("success", True),
                    error=result.get("error"),
                )
            )

    def toggle_selection(self, index: int) -> None:
        """Переключить выбор результата по индексу."""
        if 0 <= index < len(self._results):
            self._results[index].selected = not self._results[index].selected

    def select_all(self) -> None:
        """Выбрать все результаты."""
        for result in self._results:
            result.selected = True

    def deselect_all(self) -> None:
        """Снять выбор со всех результатов."""
        for result in self._results:
            result.selected = False

    def get_selected(self) -> list[TempResult]:
        """Получить выбранные результаты."""
        return [r for r in self._results if r.selected]

    def clear(self) -> None:
        """Очистить хранилище."""
        self._results.clear()
        self._current_prompt = ""

    def is_empty(self) -> bool:
        """Проверить, пустое ли хранилище."""
        return len(self._results) == 0


class ModelManager:
    """Менеджер для работы с моделями."""

    def __init__(self, db: Database):
        """
        Инициализация менеджера.

        Args:
            db: Экземпляр базы данных.
        """
        self.db = db

    def get_active_models(self) -> list[dict]:
        """Получить список активных моделей."""
        return self.db.get_models(active_only=True)

    def get_all_models(self) -> list[dict]:
        """Получить список всех моделей."""
        return self.db.get_models(active_only=False)

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
        return self.db.add_model(
            name=name,
            provider=provider,
            api_url=api_url,
            api_key_env=api_key_env,
            model_id=model_id,
            is_active=is_active,
        )

    def update_model(self, model_id: int, **kwargs) -> bool:
        """Обновить модель."""
        return self.db.update_model(model_id, **kwargs)

    def delete_model(self, model_id: int) -> bool:
        """Удалить модель."""
        return self.db.delete_model(model_id)

    def toggle_model(self, model_id: int) -> bool:
        """Переключить активность модели."""
        return self.db.toggle_model_active(model_id)

    def validate_model(self, model: dict) -> tuple[bool, str]:
        """
        Проверить корректность настроек модели.

        Args:
            model: Словарь с данными модели.

        Returns:
            Кортеж (успех, сообщение).
        """
        required_fields = ["name", "provider", "api_url", "api_key_env", "model_id"]

        for field_name in required_fields:
            if not model.get(field_name):
                return False, f"Не заполнено поле: {field_name}"

        # Проверка наличия API-ключа
        api_key = os.getenv(model["api_key_env"], "")
        if not api_key:
            return False, f"API-ключ {model['api_key_env']} не найден в переменных окружения"

        return True, "OK"

    def check_api_availability(self, model: dict) -> tuple[bool, str]:
        """
        Проверить доступность API модели.

        Args:
            model: Словарь с данными модели.

        Returns:
            Кортеж (доступен, сообщение).
        """
        client = get_client(
            provider=model["provider"],
            api_url=model["api_url"],
            api_key_env=model["api_key_env"],
            model_id=model["model_id"],
        )

        if not client.is_configured():
            return False, "API-ключ не настроен"

        return True, "API настроен"

    def add_default_models(self) -> None:
        """Добавить модели по умолчанию."""
        default_models = [
            {
                "name": "GPT-4o",
                "provider": "openai",
                "api_url": "https://api.openai.com/v1/chat",
                "api_key_env": "OPENAI_API_KEY",
                "model_id": "gpt-4o",
            },
            {
                "name": "GPT-4o-mini",
                "provider": "openai",
                "api_url": "https://api.openai.com/v1/chat",
                "api_key_env": "OPENAI_API_KEY",
                "model_id": "gpt-4o-mini",
            },
            {
                "name": "Claude 3.5 Sonnet",
                "provider": "anthropic",
                "api_url": "https://api.anthropic.com/v1/messages",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model_id": "claude-3-5-sonnet-20241022",
            },
            {
                "name": "DeepSeek Chat",
                "provider": "openai",
                "api_url": "https://api.deepseek.com/v1/chat",
                "api_key_env": "DEEPSEEK_API_KEY",
                "model_id": "deepseek-chat",
            },
            {
                "name": "Groq Llama 3.1 70B",
                "provider": "openai",
                "api_url": "https://api.groq.com/openai/v1/chat",
                "api_key_env": "GROQ_API_KEY",
                "model_id": "llama-3.1-70b-versatile",
            },
            {
                "name": "Gemini 1.5 Pro",
                "provider": "google",
                "api_url": "https://generativelanguage.googleapis.com/v1beta",
                "api_key_env": "GOOGLE_API_KEY",
                "model_id": "gemini-1.5-pro",
            },
        ]

        existing_models = {m["name"] for m in self.get_all_models()}

        for model in default_models:
            if model["name"] not in existing_models:
                self.add_model(
                    name=model["name"],
                    provider=model["provider"],
                    api_url=model["api_url"],
                    api_key_env=model["api_key_env"],
                    model_id=model["model_id"],
                    is_active=False,  # По умолчанию неактивны
                )

