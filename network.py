"""
Модуль для работы с API нейросетей.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import httpx
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


@dataclass
class APIResponse:
    """Результат запроса к API."""

    success: bool
    content: str
    tokens: int = 0
    error: Optional[str] = None


class BaseAPIClient(ABC):
    """Базовый класс для API-клиентов."""

    def __init__(
        self,
        api_url: str,
        api_key_env: str,
        model_id: str,
        timeout: int = 60,
    ):
        """
        Инициализация клиента.

        Args:
            api_url: URL эндпоинта API.
            api_key_env: Имя переменной окружения с API-ключом.
            model_id: Идентификатор модели.
            timeout: Таймаут запроса в секундах.
        """
        self.api_url = api_url
        self.api_key = os.getenv(api_key_env, "")
        self.model_id = model_id
        self.timeout = timeout

    @abstractmethod
    async def send_message(self, prompt: str) -> APIResponse:
        """
        Отправить сообщение в API.

        Args:
            prompt: Текст промпта.

        Returns:
            APIResponse с результатом.
        """
        pass

    def is_configured(self) -> bool:
        """Проверить, настроен ли клиент."""
        return bool(self.api_key)


class OpenAIClient(BaseAPIClient):
    """Клиент для OpenAI-совместимых API (OpenAI, DeepSeek, Groq, Together)."""

    async def send_message(self, prompt: str) -> APIResponse:
        """Отправить сообщение в OpenAI-совместимый API."""
        if not self.is_configured():
            return APIResponse(
                success=False,
                content="",
                error="API-ключ не настроен",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/completions",
                    headers=headers,
                    json=data,
                )
                
                # Обработка ошибок с детальным сообщением
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", str(error_data))
                    except Exception:
                        error_msg = response.text[:200]
                    return APIResponse(
                        success=False,
                        content="",
                        error=f"HTTP {response.status_code}: {error_msg}",
                    )
                
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                tokens = result.get("usage", {}).get("total_tokens", 0)

                return APIResponse(
                    success=True,
                    content=content,
                    tokens=tokens,
                )

        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                content="",
                error="Превышено время ожидания ответа",
            )
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", str(error_data))
            except Exception:
                error_msg = e.response.text[:200]
            return APIResponse(
                success=False,
                content="",
                error=f"HTTP {e.response.status_code}: {error_msg}",
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=str(e),
            )


class AnthropicClient(BaseAPIClient):
    """Клиент для Anthropic Claude API."""

    async def send_message(self, prompt: str) -> APIResponse:
        """Отправить сообщение в Anthropic API."""
        if not self.is_configured():
            return APIResponse(
                success=False,
                content="",
                error="API-ключ не настроен",
            )

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": self.model_id,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                result = response.json()

                content = result["content"][0]["text"]
                tokens = result.get("usage", {}).get("input_tokens", 0) + result.get(
                    "usage", {}
                ).get("output_tokens", 0)

                return APIResponse(
                    success=True,
                    content=content,
                    tokens=tokens,
                )

        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                content="",
                error="Превышено время ожидания ответа",
            )
        except httpx.HTTPStatusError as e:
            return APIResponse(
                success=False,
                content="",
                error=f"HTTP ошибка: {e.response.status_code}",
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=str(e),
            )


class GoogleClient(BaseAPIClient):
    """Клиент для Google Gemini API."""

    async def send_message(self, prompt: str) -> APIResponse:
        """Отправить сообщение в Google Gemini API."""
        if not self.is_configured():
            return APIResponse(
                success=False,
                content="",
                error="API-ключ не настроен",
            )

        url = f"{self.api_url}/models/{self.model_id}:generateContent?key={self.api_key}"

        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                result = response.json()

                content = result["candidates"][0]["content"]["parts"][0]["text"]
                tokens = result.get("usageMetadata", {}).get("totalTokenCount", 0)

                return APIResponse(
                    success=True,
                    content=content,
                    tokens=tokens,
                )

        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                content="",
                error="Превышено время ожидания ответа",
            )
        except httpx.HTTPStatusError as e:
            return APIResponse(
                success=False,
                content="",
                error=f"HTTP ошибка: {e.response.status_code}",
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=str(e),
            )


class OpenRouterClient(BaseAPIClient):
    """Клиент для OpenRouter API (https://openrouter.ai/)."""

    async def send_message(self, prompt: str) -> APIResponse:
        """Отправить сообщение в OpenRouter API."""
        if not self.is_configured():
            return APIResponse(
                success=False,
                content="",
                error="API-ключ не настроен",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/chatlist",
            "X-Title": "ChatList",
        }

        data = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=data,
                )
                
                # Обработка ошибок с детальным сообщением
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", str(error_data))
                    except Exception:
                        error_msg = response.text[:200]
                    return APIResponse(
                        success=False,
                        content="",
                        error=f"HTTP {response.status_code}: {error_msg}",
                    )
                
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                tokens = result.get("usage", {}).get("total_tokens", 0)

                return APIResponse(
                    success=True,
                    content=content,
                    tokens=tokens,
                )

        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                content="",
                error="Превышено время ожидания ответа",
            )
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", str(error_data))
            except Exception:
                error_msg = e.response.text[:200]
            return APIResponse(
                success=False,
                content="",
                error=f"HTTP {e.response.status_code}: {error_msg}",
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=str(e),
            )


def get_client(provider: str, api_url: str, api_key_env: str, model_id: str) -> BaseAPIClient:
    """
    Получить клиент API для указанного провайдера.

    Args:
        provider: Провайдер (openai, anthropic, google, openrouter).
        api_url: URL эндпоинта API.
        api_key_env: Имя переменной окружения с API-ключом.
        model_id: Идентификатор модели.

    Returns:
        Экземпляр клиента API.
    """
    clients = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "google": GoogleClient,
        "openrouter": OpenRouterClient,
    }

    client_class = clients.get(provider, OpenAIClient)
    return client_class(api_url, api_key_env, model_id)


async def send_to_models(
    prompt: str, models: list[dict], timeout: int = 60
) -> list[dict]:
    """
    Отправить промпт во все указанные модели.

    Args:
        prompt: Текст промпта.
        models: Список моделей из базы данных.
        timeout: Таймаут запроса в секундах.

    Returns:
        Список результатов.
    """

    async def send_single(model: dict) -> dict:
        client = get_client(
            provider=model["provider"],
            api_url=model["api_url"],
            api_key_env=model["api_key_env"],
            model_id=model["model_id"],
        )
        client.timeout = timeout

        response = await client.send_message(prompt)

        return {
            "model_id": model["id"],
            "model_name": model["name"],
            "prompt_text": prompt,
            "response": response.content if response.success else f"Ошибка: {response.error}",
            "tokens": response.tokens,
            "success": response.success,
            "error": response.error,
        }

    tasks = [send_single(model) for model in models]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Обработка исключений
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "model_id": models[i]["id"],
                "model_name": models[i]["name"],
                "prompt_text": prompt,
                "response": f"Ошибка: {str(result)}",
                "tokens": 0,
                "success": False,
                "error": str(result),
            })
        else:
            processed_results.append(result)

    return processed_results


def send_to_models_sync(
    prompt: str, models: list[dict], timeout: int = 60
) -> list[dict]:
    """
    Синхронная обёртка для send_to_models.

    Args:
        prompt: Текст промпта.
        models: Список моделей из базы данных.
        timeout: Таймаут запроса в секундах.

    Returns:
        Список результатов.
    """
    return asyncio.run(send_to_models(prompt, models, timeout))

