from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging
from .models import AnalysisRequest
from .ml_utils import predict_success
from .chat_utils import generate_recommendations
from projects.models import Project

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_analysis_task(self, analysis_request_id):
    """
    Выполняет анализ запроса, используя ML модель для предсказания успеха и ChatGPT для генерации рекомендаций.
    Обновляет статус AnalysisRequest и сохраняет результат в формате:
    {
      "success_prob": <процент успеха>,
      "recommendations": <текст рекомендаций>,
      "timestamp": <ISO-формат времени>
    }
    """
    try:
        analysis_req = AnalysisRequest.objects.get(id=analysis_request_id)
    except AnalysisRequest.DoesNotExist:
        logger.error(f"AnalysisRequest с id {analysis_request_id} не найден.")
        return

    try:
        with transaction.atomic():
            # Устанавливаем статус "processing"
            analysis_req.status = 'processing'
            analysis_req.save(update_fields=['status'])
            logger.info(f"Начало обработки AnalysisRequest id {analysis_request_id}")

            # Получаем проект и параметры анализа
            project = analysis_req.project
            params = analysis_req.params

            budget = float(params.get('budget', 0))
            competition = float(params.get('competition', 0))
            marketing_skill = float(params.get('marketing_skill', 0))
            team_experience = float(params.get('team_experience', 0))
            latitude = float(project.latitude)
            longitude = float(project.longitude)
            location_factor = float(params.get('location_factor', 0))
            extra_info = params.get('extra_info', '')

            # Вызываем ML модель для предсказания успеха
            success_prob = predict_success(
                budget, competition, marketing_skill, team_experience,
                latitude, longitude, location_factor
            )
            success_prob = float(success_prob) * 100

            # Генерируем рекомендации с помощью ChatGPT
            chatgpt_text = generate_recommendations(success_prob, extra_info=extra_info)

            final_result = {
                "success_prob": success_prob,
                "recommendations": chatgpt_text,
                "timestamp": timezone.now().isoformat(),
            }

            # Сохраняем результаты анализа
            analysis_req.result = final_result
            analysis_req.status = 'done'
            analysis_req.save(update_fields=['result', 'status'])
            logger.info(f"AnalysisRequest id {analysis_request_id} успешно обработан.")
    except Exception as e:
        logger.exception(f"Ошибка при обработке AnalysisRequest id {analysis_request_id}: {e}")
        try:
            analysis_req.status = 'error'
            analysis_req.result = {"error": str(e)}
            analysis_req.save(update_fields=['result', 'status'])
        except Exception as inner_e:
            logger.exception(f"Ошибка при обновлении статуса AnalysisRequest id {analysis_request_id}: {inner_e}")
        raise self.retry(exc=e)
