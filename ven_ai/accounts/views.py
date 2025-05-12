from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.shortcuts import render
from .forms import CustomUserRegistrationForm

User = get_user_model()

def register_view(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Генерим токен активации
            token = uuid.uuid4().hex
            user.email_verification_token = token
            user.save()

            # Формируем ссылку на активацию
            activation_link = f"http://127.0.0.1:8000/accounts/activate/{token}/"
            # На продакшене меняешь на свой домен
            subject = "Активация аккаунта"
            message = (
                f"Привет, {user.username}!\n\n"
                f"Для активации аккаунта перейди по ссылке:\n{activation_link}"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "Регистрация прошла успешно! Проверь почту для активации аккаунта.")
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def activate_account_view(request, token):
    """
    Подтверждаем регистрацию по токену, делаем is_active=True
    """
    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        messages.error(request, "Неверная или устаревшая ссылка активации!")
        return redirect('login')

    user.is_active = True
    user.email_verification_token = ""
    user.save()
    messages.success(request, "Аккаунт успешно активирован! Можете войти.")
    return redirect('login')


def profile_view(request):
    """
    Простой профиль, доступен только авторизованным юзерам
    """
    if not request.user.is_authenticated:
        messages.error(request, "Сначала войдите в систему.")
        return redirect('login')
    return render(request, 'accounts/profile.html')

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
@require_GET
def logout_view(request):
    logout(request)
    return redirect('landing')
