"""
Модуль для работы с моделями и запросами.
Содержит классы Model, Result и PromptRequest.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

from network import APIClient


# Загружаем переменные окружения
load_dotenv()


@dataclass
class Model:
    """Класс для представления модели нейросети."""
    
    id: int
    name: str
    api_url: str
    api_key_env: str
    model_id: str
    is_active: bool
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Model':
        """
        Создать объект Model из строки базы данных.
        
        Args:
            row: Строка из БД (dict)
            
        Returns:
            Объект Model
        """
        return cls(
            id=row['id'],
            name=row['name'],
            api_url=row['api_url'],
            api_key_env=row['api_key_env'],
            model_id=row['model_id'],
            is_active=bool(row['is_active'])
        )
        
    def get_api_key(self) -> Optional[str]:
        """
        Получить API ключ из переменных окружения.
        
        Returns:
            API ключ или None, если не найден
        """
        return os.getenv(self.api_key_env)
        
    def is_configured(self) -> bool:
        """
        Проверить, настроена ли модель (есть ли API ключ).
        
        Returns:
            True если API ключ найден, False иначе
        """
        return self.get_api_key() is not None


@dataclass
class Result:
    """Класс для представления результата запроса."""
    
    model_name: str
    model_id: int
    response_text: str
    response_time: Optional[float] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    selected: bool = False
    
    def is_success(self) -> bool:
        """Проверить, успешен ли результат."""
        return self.error is None and self.response_text is not None


class PromptRequest:
    """Класс для управления отправкой промпта в несколько моделей."""
    
    def __init__(self, prompt: str, models: List[Model]):
        """
        Инициализация запроса.
        
        Args:
            prompt: Текст промпта
            models: Список моделей для отправки
        """
        self.prompt = prompt
        self.models = models
        self.results: List[Result] = []
        
    def send_to_models(self, progress_callback=None) -> List[Result]:
        """
        Отправить промпт во все модели параллельно.
        
        Args:
            progress_callback: Функция для обновления прогресса (опционально)
            
        Returns:
            Список результатов
        """
        self.results = []
        
        # Фильтруем только настроенные модели
        configured_models = [m for m in self.models if m.is_configured()]
        
        if not configured_models:
            return []
        
        # Используем ThreadPoolExecutor для параллельной отправки
        with ThreadPoolExecutor(max_workers=len(configured_models)) as executor:
            # Создаём задачи
            future_to_model = {
                executor.submit(self._send_to_single_model, model): model
                for model in configured_models
            }
            
            # Собираем результаты по мере выполнения
            for future in as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    # Вызываем callback для обновления UI
                    if progress_callback:
                        progress_callback(model.name, result)
                        
                except Exception as e:
                    # Добавляем результат с ошибкой
                    error_result = Result(
                        model_name=model.name,
                        model_id=model.id,
                        response_text="",
                        error=f"Исключение: {str(e)}"
                    )
                    self.results.append(error_result)
                    
                    if progress_callback:
                        progress_callback(model.name, error_result)
        
        return self.results
        
    def _send_to_single_model(self, model: Model) -> Result:
        """
        Отправить промпт в одну модель.
        
        Args:
            model: Модель для отправки
            
        Returns:
            Результат запроса
        """
        api_key = model.get_api_key()
        
        if not api_key:
            return Result(
                model_name=model.name,
                model_id=model.id,
                response_text="",
                error=f"API ключ {model.api_key_env} не найден в .env"
            )
        
        try:
            client = APIClient(model.api_url, api_key, model.model_id)
            response_text, response_time, tokens, error = client.send_request(self.prompt)
            
            return Result(
                model_name=model.name,
                model_id=model.id,
                response_text=response_text or "",
                response_time=response_time,
                tokens_used=tokens,
                error=error
            )
            
        except Exception as e:
            return Result(
                model_name=model.name,
                model_id=model.id,
                response_text="",
                error=f"Ошибка: {str(e)}"
            )
            
    def get_results(self) -> List[Result]:
        """Получить список результатов."""
        return self.results
        
    def get_successful_results(self) -> List[Result]:
        """Получить только успешные результаты."""
        return [r for r in self.results if r.is_success()]
        
    def get_selected_results(self) -> List[Result]:
        """Получить только выбранные результаты."""
        return [r for r in self.results if r.selected]


if __name__ == '__main__':
    print("Модуль models.py готов к использованию")

