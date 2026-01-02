"""
Модуль для отправки запросов к API нейросетей.
Поддерживает различные API (OpenAI, DeepSeek, Groq и др.).
"""

import requests
import time
from typing import Dict, Optional, Tuple
from config import API_TIMEOUT, MAX_RETRIES


class APIClient:
    """Клиент для отправки запросов к API нейросетей."""
    
    def __init__(self, api_url: str, api_key: str, model_id: str):
        """
        Инициализация клиента API.
        
        Args:
            api_url: URL эндпоинта API
            api_key: API ключ для аутентификации
            model_id: Идентификатор модели
        """
        self.api_url = api_url
        self.api_key = api_key
        self.model_id = model_id
        self.api_type = self._detect_api_type(api_url)
        
    def _detect_api_type(self, url: str) -> str:
        """
        Определить тип API по URL.
        
        Args:
            url: URL эндпоинта
            
        Returns:
            Тип API: 'openai', 'deepseek', 'groq' или 'generic'
        """
        url_lower = url.lower()
        if 'openai.com' in url_lower:
            return 'openai'
        elif 'deepseek.com' in url_lower:
            return 'deepseek'
        elif 'groq.com' in url_lower:
            return 'groq'
        elif 'anthropic.com' in url_lower:
            return 'anthropic'
        else:
            return 'generic'
            
    def send_request(self, prompt: str) -> Tuple[Optional[str], Optional[float], Optional[int], Optional[str]]:
        """
        Отправить запрос к API.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Кортеж: (текст_ответа, время_ответа, количество_токенов, текст_ошибки)
        """
        start_time = time.time()
        
        try:
            # Формируем запрос в зависимости от типа API
            headers, payload = self._prepare_request(prompt)
            
            # Отправляем запрос с повторными попытками
            response = self._send_with_retry(headers, payload)
            
            # Обрабатываем ответ
            response_time = time.time() - start_time
            response_text, tokens = self._parse_response(response)
            
            return response_text, response_time, tokens, None
            
        except requests.exceptions.Timeout:
            return None, None, None, "Превышено время ожидания ответа"
        except requests.exceptions.ConnectionError:
            return None, None, None, "Ошибка подключения к API"
        except requests.exceptions.HTTPError as e:
            return None, None, None, f"HTTP ошибка: {e}"
        except Exception as e:
            return None, None, None, f"Неизвестная ошибка: {str(e)}"
            
    def _prepare_request(self, prompt: str) -> Tuple[Dict, Dict]:
        """
        Подготовить заголовки и данные запроса.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Кортеж: (заголовки, данные)
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Формат для OpenAI-совместимых API
        if self.api_type in ['openai', 'deepseek', 'groq']:
            payload = {
                'model': self.model_id,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7
            }
        # Формат для Anthropic Claude
        elif self.api_type == 'anthropic':
            headers['x-api-key'] = self.api_key
            headers['anthropic-version'] = '2023-06-01'
            del headers['Authorization']
            payload = {
                'model': self.model_id,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 4096
            }
        else:
            # Универсальный формат
            payload = {
                'model': self.model_id,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }
            
        return headers, payload
        
    def _send_with_retry(self, headers: Dict, payload: Dict) -> requests.Response:
        """
        Отправить запрос с повторными попытками.
        
        Args:
            headers: HTTP заголовки
            payload: Данные запроса
            
        Returns:
            Ответ от сервера
        """
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                return response
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))  # Экспоненциальная задержка
                    
        raise last_exception
        
    def _parse_response(self, response: requests.Response) -> Tuple[str, Optional[int]]:
        """
        Извлечь текст ответа и количество токенов.
        
        Args:
            response: Ответ от сервера
            
        Returns:
            Кортеж: (текст_ответа, количество_токенов)
        """
        data = response.json()
        
        # Для OpenAI-совместимых API
        if self.api_type in ['openai', 'deepseek', 'groq']:
            response_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            tokens = data.get('usage', {}).get('total_tokens')
            
        # Для Anthropic Claude
        elif self.api_type == 'anthropic':
            response_text = data.get('content', [{}])[0].get('text', '')
            tokens = data.get('usage', {}).get('input_tokens', 0) + data.get('usage', {}).get('output_tokens', 0)
            
        else:
            # Попытка универсального парсинга
            response_text = (
                data.get('choices', [{}])[0].get('message', {}).get('content', '') or
                data.get('content', [{}])[0].get('text', '') or
                str(data)
            )
            tokens = data.get('usage', {}).get('total_tokens')
            
        return response_text, tokens


def test_api_connection(api_url: str, api_key: str, model_id: str) -> bool:
    """
    Проверить подключение к API.
    
    Args:
        api_url: URL эндпоинта
        api_key: API ключ
        model_id: ID модели
        
    Returns:
        True если подключение успешно, False иначе
    """
    try:
        client = APIClient(api_url, api_key, model_id)
        response_text, _, _, error = client.send_request("Привет!")
        return error is None and response_text is not None
    except:
        return False


if __name__ == '__main__':
    # Тестирование (требует реальный API ключ)
    print("Модуль network.py готов к использованию")

