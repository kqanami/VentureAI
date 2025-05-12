import os
import joblib
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict
import openai
from django.conf import settings

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Настройка API ключа для OpenAI
openai.api_key = settings.OPENAI_API_KEY

# Формирование пути к модели с использованием pathlib
MODEL_PATH = Path(settings.BASE_DIR) / 'analysis' / 'model.pkl'
try:
    model_pipeline = joblib.load(str(MODEL_PATH))
    logger.info("Модель успешно загружена из %s", MODEL_PATH)
except Exception as e:
    logger.exception("Ошибка загрузки модели: %s", e)
    model_pipeline = None


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
                      или, если в процентах (например, 75), оставляется как есть.
        extra_info: Дополнительная информация для генерации рекомендаций.

    Returns:
        Строка с рекомендациями, сгенерированными ChatGPT.
    """
    # Если success_prob передается как доля (например, 0.75), преобразуем в проценты.
    display_prob = round(success_prob * 100) if success_prob <= 1 else round(success_prob)

    messages = [
        {"role": "system", "content": (
            "Ты - эксперт в бизнес-аналитике и стратегическом планировании. "
            "Учитывай всю дополнительную информацию, предоставленную пользователем, и давай подробные рекомендации по развитию бизнеса."
        )},
        {"role": "user", "content": (
            f"Вероятность успеха: ~{display_prob}%. Дополнительная информация: {extra_info}. "
            "Дай подробные рекомендации по развитию бизнеса с учётом всех указанных данных."
        )}
    ]
    try:
        recommendations = chatgpt_conversation(messages)
        return recommendations
    except Exception as e:
        logger.exception("Ошибка при генерации рекомендаций")
        return "Произошла ошибка при генерации рекомендаций. Попробуйте позже."


def generate_business_plan(extra_info: str) -> str:
    """
    Генерирует пошаговый план развития бизнеса на основе дополнительной информации, предоставленной пользователем.
    Если дополнительная информация отсутствует, возвращает сообщение об этом.

    Args:
        extra_info (str): Дополнительная информация от пользователя.

    Returns:
        str: Пошаговый план развития бизнеса или сообщение о недостатке информации.
    """
    if not extra_info.strip():
        return "Дополнительная информация не предоставлена. Пошаговый план развития бизнеса не может быть сформирован."

    steps = [
        f"Проанализируйте предоставленную информацию: {extra_info}",
        "Определите ключевые точки роста и целевые аудитории.",
        "Разработайте маркетинговую стратегию с учётом уровня конкуренции.",
        "Сформируйте бюджет и распределите ресурсы оптимально.",
        "Организуйте команду и четко распределите обязанности.",
        "Установите KPI и разработайте систему мониторинга результатов.",
        "Запустите пилотные проекты для проверки гипотез.",
        "Анализируйте результаты и корректируйте стратегию по необходимости."
    ]
    plan = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))
    return plan
