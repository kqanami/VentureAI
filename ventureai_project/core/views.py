import openai
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, BusinessProjectForm
from django.contrib import messages
from .models import BusinessProject, ProjectAnalysis, ProjectComment
from django.conf import settings
import json
from django.views.decorators.http import require_POST
from .utils.maps import get_similar_businesses
from .utils.ai_assistant import get_business_advice

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно.")
            return redirect('core:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Вход выполнен успешно.")
                return redirect('core:dashboard')
        messages.error(request, "Неправильные email или пароль.")
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('core:login')

@login_required
def dashboard(request):
    projects = BusinessProject.objects.filter(user=request.user)
    return render(request, 'core/dashboard.html', {'projects': projects})

@login_required
def project_create(request):
    if request.method == 'POST':
        form = BusinessProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            messages.success(request, "Проект создан успешно.")
            return redirect('core:dashboard')
    else:
        form = BusinessProjectForm()
    return render(request, 'core/project_form.html', {'form': form})

@login_required
def project_update(request, pk):
    project = BusinessProject.objects.get(pk=pk, user=request.user)
    if request.method == 'POST':
        form = BusinessProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Проект обновлён успешно.")
            return redirect('core:dashboard')
    else:
        form = BusinessProjectForm(instance=project)
    return render(request, 'core/project_form.html', {'form': form})

@login_required
def project_delete(request, pk):
    project = BusinessProject.objects.get(pk=pk, user=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Проект удалён успешно.")
        return redirect('core:dashboard')
    return render(request, 'core/project_confirm_delete.html', {'project': project})


@login_required
def project_analyze(request, pk):
    # Получение проекта или возврат 404, если не найден
    project = get_object_or_404(BusinessProject, pk=pk, user=request.user)

    # Проверка наличия токенов
    if request.user.tokens <= 0:
        messages.error(request, "У вас недостаточно токенов для анализа.")
        return redirect('core:dashboard')

    # Установка API-ключа OpenAI
    openai.api_key = settings.OPENAI_API_KEY

    # Формирование сообщений для модели чата
    messages_chat = [
        {"role": "system", "content": "Ты полезный помощник, оценивающий жизнеспособность бизнес-идей."},
        {"role": "user", "content": f"""
        Оцените жизнеспособность бизнес-идеи:
        Название: {project.name}
        Описание: {project.description}
        Бюджет: {project.budget}
        Локация: {project.location}
        Уровень конкуренции: {project.competition_level}/5

        Предоставьте вероятность успеха в процентах и рекомендации для улучшения в следующем формате:
        {{
            "success_probability": число,
            "recommendations": строка
        }}
        """}
    ]

    try:
        # Вызов ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_chat,
            max_tokens=150,
            temperature=0.7,
        )

        # Извлечение ответа модели
        result = response.choices[0].message['content'].strip()

        # Попытка разобрать ответ как JSON
        analysis_data = json.loads(result)

        success_probability = analysis_data.get('success_probability', 0.0)
        recommendations = analysis_data.get('recommendations', '')

        # Сохранение анализа в базе данных
        ProjectAnalysis.objects.create(
            project=project,
            success_probability=success_probability,
            recommendations=recommendations
        )

        # Списание одного токена у пользователя
        request.user.tokens -= 1
        request.user.save()

        messages.success(request, f"Анализ завершён. Вероятность успеха: {success_probability}%.")
    except json.JSONDecodeError:
        # Обработка случая, когда ответ не является валидным JSON
        messages.error(request, "Не удалось разобрать ответ от модели. Пожалуйста, попробуйте снова.")
    except openai.error.OpenAIError as e:
        # Обработка ошибок OpenAI API
        messages.error(request, f"Ошибка при обращении к OpenAI: {str(e)}")
    except Exception as e:
        # Обработка других возможных ошибок
        messages.error(request, f"Ошибка при анализе проекта: {str(e)}")

    return redirect('core:dashboard')

@login_required
def buy_tokens(request):
    if request.method == 'POST':
        try:
            tokens_to_add = int(request.POST.get('tokens'))
            # Здесь должна быть интеграция с платёжной системой (Stripe, PayPal и т.д.)
            # Для упрощения предположим, что оплата прошла успешно
            request.user.tokens += tokens_to_add
            request.user.save()
            messages.success(request, f"Вы успешно купили {tokens_to_add} токенов.")
            return redirect('core:dashboard')
        except:
            messages.error(request, "Произошла ошибка при покупке токенов.")
    return render(request, 'core/buy_tokens.html')

@require_POST
@login_required
def add_comment(request, pk):
    project = get_object_or_404(BusinessProject, pk=pk, user=request.user)
    comment_text = request.POST.get('comment')
    rating = request.POST.get('rating')
    if comment_text:
        ProjectComment.objects.create(
            project=project,
            user=request.user,
            comment=comment_text,
            rating=int(rating) if rating and rating.isdigit() else 0
        )
        messages.success(request, "Комментарий добавлен.")
    else:
        messages.error(request, "Комментарий не может быть пустым.")
    return redirect('core:dashboard')


@login_required
def similar_businesses(request):
    # Для примера: можно передавать координаты через GET-параметры
    latitude = request.GET.get('lat', None)
    longitude = request.GET.get('lng', None)
    businesses = []

    if latitude and longitude:
        try:
            businesses = get_similar_businesses(latitude, longitude)
        except Exception as e:
            businesses = []
            error = str(e)
    else:
        error = "Не заданы координаты."

    context = {
        'businesses': businesses,
        'error': error if 'error' in locals() else None
    }
    return render(request, 'core/similar_businesses.html', context)

@login_required
def business_advice(request):
    advice = None
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        if prompt:
            advice = get_business_advice(prompt)
    return render(request, 'core/ai_assistant.html', {'advice': advice})