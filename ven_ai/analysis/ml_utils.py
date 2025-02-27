import os
import joblib
import numpy as np
import pandas as pd
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'analysis', '../model.pkl')
try:
    model_pipeline = joblib.load(MODEL_PATH)
    logger.info("Модель успешно загружена из %s", MODEL_PATH)
except Exception as e:
    logger.exception("Ошибка загрузки модели: %s", e)
    model_pipeline = None

def predict_success(
    budget: float,
    competition: float,
    marketing_skill: float,
    team_experience: float,
    latitude: float,
    longitude: float,
    location_factor: float
) -> float:
    """
    Принимает 7 параметров и возвращает вероятность успеха.

    Args:
        budget (float): Бюджет проекта.
        competition (float): Уровень конкуренции.
        marketing_skill (float): Навык маркетинга.
        team_experience (float): Опыт команды.
        latitude (float): Широта проекта.
        longitude (float): Долгота проекта.
        location_factor (float): Фактор локации.

    Returns:
        float: Вероятность успеха (от 0 до 1).

    Raises:
        ValueError: Если модель не загружена или произошла ошибка при прогнозировании.
    """
    if model_pipeline is None:
        logger.error("Модель не загружена, прогнозирование невозможно.")
        raise ValueError("Модель не загружена.")

    try:
        # Формируем DataFrame с именами столбцов, как в обучении модели
        data = {
            'budget': [budget],
            'competition': [competition],
            'marketing_skill': [marketing_skill],
            'team_experience': [team_experience],
            'latitude': [latitude],
            'longitude': [longitude],
            'location_factor': [location_factor],
        }
        X_input = pd.DataFrame(data)
        # Трансформеры внутри pipeline (например, GeoDistanceTransformer) подберут нужные столбцы
        probabilities = model_pipeline.predict_proba(X_input)[0]
        success_probability = float(probabilities[1])
        logger.info("Прогнозирование выполнено успешно: %.4f", success_probability)
        return success_probability
    except Exception as e:
        logger.exception("Ошибка при прогнозировании успеха: %s", e)
        raise ValueError(f"Ошибка при прогнозировании успеха: {e}") from e
