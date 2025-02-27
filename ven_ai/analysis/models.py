from django.db import models
from django.conf import settings
from projects.models import Project

class AnalysisRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'В очереди'),
        ('processing', 'Обработка'),
        ('done', 'Завершено'),
        ('error', 'Ошибка'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name='Проект'
    )
    params = models.JSONField(default=dict, blank=True, verbose_name='Параметры анализа')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    result = models.JSONField(default=dict, blank=True, verbose_name='Результат')
    chat_history = models.JSONField(default=list, blank=True, verbose_name='История чата')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    def __str__(self):
        return f"AnalysisRequest #{self.id} for {self.project.name}"

    def start_analysis(self):
        """
        Запускаем асинхронную задачу Celery (или можно синхронно).
        """
        from .tasks import run_analysis_task
        self.status = 'pending'
        self.save()
        run_analysis_task.delay(self.id)
