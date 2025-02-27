from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class CustomUser(AbstractUser):
    """
    Расширенная модель. У нас дополнительные поля:
    - tokens: кол-во токенов на аккаунте
    - free_analysis_count: счётчик бесплатных анализов (по умолчанию 3)
    - email_verification_token: ключик для активации через email
    - is_active: пользователь становится активным только после активации
    """
    tokens = models.IntegerField(default=0)
    free_analysis_count = models.IntegerField(default=3)
    email_verification_token = models.CharField(max_length=64, null=True, blank=True)


    def __str__(self):
        return self.username
