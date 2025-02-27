import openai
import logging
from typing import List, Dict
from django.conf import settings

# Настраиваем логгер
logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

def chatgpt_conversation(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7
) -> str:
    """
    Выполняет запрос к OpenAI ChatCompletion API с заданными сообщениями.

    Args:
        messages: Список сообщений в формате [{'role': 'system'|'user'|'assistant', 'content': '...'}, ...].
        model: Модель для использования (по умолчанию "gpt-3.5-turbo").
        temperature: Параметр температуры, влияющий на креативность ответа.

    Returns:
        Ответ от assistant в виде строки.

    Raises:
        Exception: Если запрос к API завершился ошибкой.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        if not response.choices:
            raise ValueError("Получен пустой ответ от OpenAI")
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        logger.exception("Ошибка при вызове OpenAI ChatCompletion API")
        raise

def generate_recommendations(success_prob: float, extra_info: str = "") -> str:
    """
    Генерирует рекомендации по развитию на основе вероятности успеха и дополнительной информации.

    Args:
        success_prob: Вероятность успеха. Ожидается, что значение передается как доля (например, 0.75)
                      или, если в процентах (например, 75), раскомментируйте нужную строку.
        extra_info: Дополнительная информация для генерации рекомендаций.

    Returns:
        Строка с рекомендациями, сгенерированными ChatGPT.
    """
    # Если success_prob передается в процентах (например, 75), то преобразуй в долю (0.75)
    # success_prob = success_prob / 100 if success_prob > 1 else success_prob

    # Формируем сообщения для ChatGPT
    messages = [
        {"role": "system", "content": "Ты - эксперт в бизнес-аналитике."},
        {"role": "user", "content": (
            f"Вероятность успеха: ~{round(success_prob * 100)}%. Доп. информация: {extra_info}. "
            "Дай рекомендации по развитию."
        )}
    ]
    try:
        recommendations = chatgpt_conversation(messages)
        return recommendations
    except Exception as e:
        logger.exception("Ошибка при генерации рекомендаций")
        return "Произошла ошибка при генерации рекомендаций. Попробуйте позже."
