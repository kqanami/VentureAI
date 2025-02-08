from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    tokens = models.IntegerField(default=3)  # Начальное количество токенов

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class BusinessProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    competition_level = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Правильное имя поля
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class ProjectAnalysis(models.Model):
    project = models.ForeignKey(BusinessProject, on_delete=models.CASCADE, related_name='analyses')
    success_probability = models.FloatField()
    recommendations = models.TextField()
    analyzed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Analysis of {self.project.name} at {self.analyzed_at}"

class ProjectComment(models.Model):
    project = models.ForeignKey(BusinessProject, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.PositiveSmallIntegerField(default=0)  # Например, оценка от 0 до 5
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Комментарий от {self.user.username} к {self.project.name}"