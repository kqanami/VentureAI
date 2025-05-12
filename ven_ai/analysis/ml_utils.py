import os
import joblib
import numpy as np
import pandas as pd
import logging
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

# Формирование пути к модели с использованием pathlib
MODEL_PATH = Path(settings.BASE_DIR) / 'analysis' / 'model.pkl'
try:
    model_pipeline = joblib.load(str(MODEL_PATH))
    logger.info("Модель успешно загружена из %s", MODEL_PATH)
except Exception as e:
    logger.exception("Ошибка загрузки модели: %s", e)
    model_pipeline = None


def generate_business_plan(extra_info: str) -> str:
    """
    Генерирует пошаговый план развития бизнеса на основе дополнительной информации, предоставленной пользователем.

    Args:
        extra_info (str): Дополнительная информация от пользователя.

    Returns:
        str: Пошаговый план развития бизнеса.
    """
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
    # Формируем план с шагами
    plan = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))
    return plan


def predict_success(
        budget: float,
        competition: float,
        marketing_skill: float,
        team_experience: float,
        latitude: float,
        longitude: float,
        location_factor: float,
        extra_info: str = None
) -> dict:
    """
    Принимает параметры для прогнозирования успеха проекта и дополнительную информацию для генерации бизнес-плана.

    Args:
        budget (float): Бюджет проекта.
        competition (float): Уровень конкуренции.
        marketing_skill (float): Навык маркетинга.
        team_experience (float): Опыт команды.
        latitude (float): Широта проекта.
        longitude (float): Долгота проекта.
        location_factor (float): Фактор локации.
        extra_info (str, optional): Дополнительная информация от пользователя для формирования бизнес-плана.

    Returns:
        dict: {
            "success_probability": float,  # Вероятность успеха проекта (от 0 до 1).
            "business_plan": str             # Пошаговый план развития бизнеса (если extra_info передана, иначе пустая строка).
        }

    Raises:
        ValueError: Если модель не загружена или произошла ошибка при прогнозировании.
    """
    if model_pipeline is None:
        logger.error("Модель не загружена, прогнозирование невозможно.")
        raise ValueError("Модель не загружена.")

    try:
        logger.debug(
            "Начало прогнозирования с параметрами: budget=%s, competition=%s, marketing_skill=%s, team_experience=%s, latitude=%s, longitude=%s, location_factor=%s, extra_info=%s",
            budget, competition, marketing_skill, team_experience, latitude, longitude, location_factor, extra_info
        )

        # Формируем DataFrame с теми же столбцами, что и при обучении модели
        input_data = pd.DataFrame({
            'budget': [budget],
            'competition': [competition],
            'marketing_skill': [marketing_skill],
            'team_experience': [team_experience],
            'latitude': [latitude],
            'longitude': [longitude],
            'location_factor': [location_factor],
        })
        logger.debug("Сформированный DataFrame: %s", input_data.to_dict(orient='list'))

        # Прогнозируем вероятность успеха
        if hasattr(model_pipeline, 'predict_proba'):
            probabilities = model_pipeline.predict_proba(input_data)[0]
            success_probability = float(probabilities[1])
        else:
            prediction = model_pipeline.predict(input_data)[0]
            success_probability = float(prediction)

        # Гарантируем, что вероятность находится в диапазоне [0, 1]
        success_probability = max(0.0, min(1.0, success_probability))
        logger.info("Прогнозирование выполнено успешно: вероятность успеха = %.4f", success_probability)

        # Генерация бизнес-плана, если предоставлена дополнительная информация
        business_plan = ""
        if extra_info and extra_info.strip():
            business_plan = generate_business_plan(extra_info)
            logger.info("Бизнес-план сгенерирован успешно.")

        return {
            "success_probability": success_probability,
            "business_plan": business_plan
        }

    except Exception as e:
        logger.exception("Ошибка при прогнозировании успеха: %s", e)
        raise ValueError(f"Ошибка при прогнозировании успеха: {e}") from e
