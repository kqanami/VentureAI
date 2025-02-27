from django.db import models
from django.conf import settings
# from django.utils.text import slugify  # если вдруг захочешь слаги

class Project(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='Владелец'
    )
    name = models.CharField(max_length=255, verbose_name='Название проекта')
    description = models.TextField(verbose_name='Описание')
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Бюджет')
    location = models.CharField(max_length=255, verbose_name='Локация')  # можно сделать геополе, если надо
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # Пример ManyToMany для коллабораций (необязательно)
    # collaborators = models.ManyToManyField(
    #     settings.AUTH_USER_MODEL,
    #     related_name='collaborations',
    #     blank=True
    # )

    # Пример прикрепления файла (опционально)
    # file_upload = models.FileField(upload_to='project_files/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-created_at']  # сортировка по дате создания, последние сверху
