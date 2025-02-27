from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Поля, которые хотим видеть в админке
    list_display = ('username', 'email', 'is_active', 'tokens', 'free_analysis_count')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')

    # Расширяем поля в форме редактирования пользователя
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Токены и анализы', {'fields': ('tokens', 'free_analysis_count')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
