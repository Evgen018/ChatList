"""
Модуль логики работы с моделями.
"""

import os
import re
import asyncio
from dataclasses import dataclass, field
from typing import Optional

from db import Database
from network import get_client, OpenRouterClient


# Системный промпт для AI-ассистента улучшения промптов
IMPROVE_SYSTEM_PROMPT = """Ты — эксперт по улучшению промптов для языковых моделей.

Твоя задача — проанализировать промпт пользователя и предложить улучшенные версии.

ФОРМАТ ОТВЕТА (строго соблюдай):

## УЛУЧШЕННЫЙ ПРОМПТ
[Здесь улучшенная версия оригинального промпта — более чёткая, структурированная и эффективная]

## АЛЬТЕРНАТИВА 1: Для кода/технических задач
[Версия промпта, оптимизированная для программирования и технического анализа]

## АЛЬТЕРНАТИВА 2: Для анализа/исследования  
[Версия промпта для глубокого анализа и детального исследования темы]

## АЛЬТЕРНАТИВА 3: Для креатива/контента
[Версия промпта для творческих задач, генерации идей, написания текстов]

ПРАВИЛА:
- Сохраняй смысл оригинального запроса
- Добавляй контекст и конкретику
- Указывай желаемый формат ответа
- Используй ролевые инструкции ("Ты — эксперт по...")
- Разбивай сложные задачи на шаги
- Каждая версия должна быть самодостаточной"""


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


@dataclass
class ImprovedPrompt:
    """Результат улучшения промпта."""
    
    original: str
    improved: str
    alternatives: list[str] = field(default_factory=list)
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
        """Получить текущий промпт."""
        return self._current_prompt

    def set_results(self, prompt: str, results: list[dict]) -> None:
        """
        Установить новые результаты.

        Args:
            prompt: Текст промпта.
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
        """Добавить модели по умолчанию (бесплатные через OpenRouter)."""
        default_models = [
            # OpenRouter — бесплатные модели (FREE) - актуальный список
            {
                "name": "DeepSeek R1 (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "deepseek/deepseek-r1-0528:free",
            },
            {
                "name": "Qwen3 4B (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "qwen/qwen3-4b:free",
            },
            {
                "name": "Qwen3 Coder (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "qwen/qwen3-coder:free",
            },
            {
                "name": "Google Gemma 3n E4B (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "google/gemma-3n-e4b-it:free",
            },
            {
                "name": "Mistral Devstral (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "mistralai/devstral-2512:free",
            },
            {
                "name": "Kimi K2 (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "moonshotai/kimi-k2:free",
            },
            {
                "name": "Nvidia Nemotron 9B (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "nvidia/nemotron-nano-9b-v2:free",
            },
            {
                "name": "Dolphin Mistral 24B (free)",
                "provider": "openrouter",
                "api_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "model_id": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
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


class PromptImprover:
    """AI-ассистент для улучшения промптов."""

    # Модели OpenRouter, рекомендуемые для улучшения промптов (бесплатные, актуальные)
    RECOMMENDED_MODELS = [
        ("DeepSeek R1", "deepseek/deepseek-r1-0528:free"),
        ("Qwen3 4B", "qwen/qwen3-4b:free"),
        ("Qwen3 Coder", "qwen/qwen3-coder:free"),
        ("Google Gemma 3n E4B", "google/gemma-3n-e4b-it:free"),
        ("Google Gemma 3n E2B", "google/gemma-3n-e2b-it:free"),
        ("Mistral Devstral", "mistralai/devstral-2512:free"),
        ("Kimi K2", "moonshotai/kimi-k2:free"),
        ("Nvidia Nemotron 9B", "nvidia/nemotron-nano-9b-v2:free"),
    ]

    def __init__(self, db: Database):
        """
        Инициализация улучшателя промптов.

        Args:
            db: Экземпляр базы данных для получения настроек.
        """
        self.db = db

    def get_selected_model(self) -> str:
        """Получить выбранную модель для улучшения."""
        return self.db.get_setting(
            "improve_model", 
            self.RECOMMENDED_MODELS[0][1]  # По умолчанию первая модель
        )

    def set_selected_model(self, model_id: str) -> None:
        """Установить модель для улучшения."""
        self.db.set_setting("improve_model", model_id)

    async def improve_async(self, original_prompt: str, timeout: int = 90) -> ImprovedPrompt:
        """
        Улучшить промпт асинхронно.

        Args:
            original_prompt: Исходный промпт пользователя.
            timeout: Таймаут запроса в секундах.

        Returns:
            ImprovedPrompt с улучшенной версией и альтернативами.
        """
        model_id = self.get_selected_model()
        
        # Создаём клиент OpenRouter
        client = OpenRouterClient(
            api_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            model_id=model_id,
            timeout=timeout,
        )

        if not client.is_configured():
            return ImprovedPrompt(
                original=original_prompt,
                improved="",
                success=False,
                error="API-ключ OPENROUTER_API_KEY не настроен",
            )

        # Формируем запрос с системным промптом
        full_prompt = f"""{IMPROVE_SYSTEM_PROMPT}

ПРОМПТ ПОЛЬЗОВАТЕЛЯ:
{original_prompt}

Проанализируй и предложи улучшенные версии."""

        response = await client.send_message(full_prompt)

        if not response.success:
            return ImprovedPrompt(
                original=original_prompt,
                improved="",
                success=False,
                error=response.error,
            )

        # Проверяем, что ответ не пустой
        if not response.content or not response.content.strip():
            return ImprovedPrompt(
                original=original_prompt,
                improved="",
                success=False,
                error="AI вернул пустой ответ. Попробуйте другую модель.",
            )

        # Парсим ответ
        return self._parse_response(original_prompt, response.content)

    def improve_sync(self, original_prompt: str, timeout: int = 90) -> ImprovedPrompt:
        """
        Синхронная обёртка для improve_async.

        Args:
            original_prompt: Исходный промпт пользователя.
            timeout: Таймаут запроса в секундах.

        Returns:
            ImprovedPrompt с улучшенной версией и альтернативами.
        """
        return asyncio.run(self.improve_async(original_prompt, timeout))

    def _parse_response(self, original: str, response_text: str) -> ImprovedPrompt:
        """
        Распарсить ответ AI в структурированный формат.

        Args:
            original: Оригинальный промпт.
            response_text: Текст ответа от AI.

        Returns:
            ImprovedPrompt со всеми вариантами.
        """
        # Если ответ пустой — ошибка
        if not response_text or not response_text.strip():
            return ImprovedPrompt(
                original=original,
                improved="",
                success=False,
                error="Получен пустой ответ от AI",
            )

        improved = ""
        alternatives = []

        # Паттерны для поиска улучшенного промпта (разные форматы)
        improved_patterns = [
            r"##\s*УЛУЧШЕННЫЙ ПРОМПТ[:\s]*\n(.*?)(?=##\s*АЛЬТЕРНАТИВА|\Z)",
            r"\*\*УЛУЧШЕННЫЙ ПРОМПТ[:\s]*\*\*\s*\n(.*?)(?=\*\*АЛЬТЕРНАТИВА|\Z)",
            r"(?:^|\n)1[\.\)]\s*(.*?)(?=\n2[\.\)]|\Z)",  # Нумерованный список
            r"Улучшенн[аы][яй]?\s*(?:версия|промпт)[:\s]*(.*?)(?=Альтернатив|\Z)",
        ]

        for pattern in improved_patterns:
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                improved = match.group(1).strip()
                if improved:
                    break

        # Паттерны для альтернатив
        alt_patterns = [
            r"##\s*АЛЬТЕРНАТИВА\s*\d+[^#\n]*\n(.*?)(?=##\s*АЛЬТЕРНАТИВА|\Z)",
            r"\*\*АЛЬТЕРНАТИВА\s*\d+[^*\n]*\*\*\s*\n(.*?)(?=\*\*АЛЬТЕРНАТИВА|\Z)",
            r"(?:^|\n)[2-4][\.\)]\s*(.*?)(?=\n[3-5][\.\)]|\Z)",  # Нумерованный список 2-4
        ]

        for pattern in alt_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                alt_text = match.strip()
                if alt_text and len(alt_text) > 10:  # Минимальная длина
                    alternatives.append(alt_text)
            if alternatives:
                break

        # Если парсинг не удался — используем весь ответ как улучшенную версию
        if not improved:
            # Убираем служебные заголовки и берём основной текст
            cleaned = response_text.strip()
            # Убираем маркеры типа "## УЛУЧШЕННЫЙ ПРОМПТ" если они есть
            cleaned = re.sub(r'^#+\s*.*?\n', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'^\*\*.*?\*\*\s*\n', '', cleaned, flags=re.MULTILINE)
            improved = cleaned.strip() if cleaned.strip() else response_text.strip()

        return ImprovedPrompt(
            original=original,
            improved=improved,
            alternatives=alternatives,
            success=True,
        )

