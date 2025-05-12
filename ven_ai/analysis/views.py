from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import AnalysisRequest
from .forms import AnalysisForm
from .chat_utils import chatgpt_conversation  # для scenario_chat
from projects.models import Project


@login_required
def create_analysis_request_view(request, project_id):
    """
    Форма для ввода параметров, создаём AnalysisRequest, списываем анализы/токены.
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            # Списываем бесплатные анализы или токены
            if request.user.free_analysis_count > 0:
                request.user.free_analysis_count -= 1
                request.user.save()
            else:
                if request.user.tokens <= 0:
                    messages.error(request, "У вас нет доступных анализов! Купите токены.")
                    return redirect('buy_tokens')
                request.user.tokens -= 1
                request.user.save()

            # Собираем параметры из формы + координаты из Project
            data = {
                'budget': form.cleaned_data['budget'],
                'competition': form.cleaned_data['competition'],
                'location_factor': form.cleaned_data['location_factor'],
                'marketing_skill': form.cleaned_data['marketing_skill'],
                'team_experience': form.cleaned_data['team_experience'],
                # Координаты берем из project (БД)
                'latitude': float(project.latitude) if project.latitude is not None else None,
                'longitude': float(project.longitude) if project.longitude is not None else None,
                # Дополнительная информация для бизнес-плана и рекомендаций
                'extra_info': form.cleaned_data.get('extra_info', '')
            }

            # Создаём AnalysisRequest
            analysis_req = AnalysisRequest.objects.create(
                user=request.user,
                project=project,
                params=data,
                status='pending'
            )
            # Запускаем Celery-задачу
            analysis_req.start_analysis()

            messages.success(request, "Заявка на анализ создана! Подождите некоторое время для результатов.")
            return redirect('analysis_detail', analysis_request_id=analysis_req.id)
    else:
        # Задаем начальные значения полей формы из проекта
        form = AnalysisForm(initial={
             'budget': project.budget,
             'latitude': project.latitude,
             'longitude': project.longitude,
             # Начальное значение для extra_info можно задать, если нужно
             'extra_info': ''
        })

    return render(request, 'analysis/analysis_form.html', {
        'form': form,
        'project': project,
    })


@login_required
def analysis_detail_view(request, analysis_request_id):
    """
    Смотрим статус и результат анализа.
    """
    analysis_req = get_object_or_404(AnalysisRequest, id=analysis_request_id, user=request.user)
    return render(request, 'analysis/analysis_detail.html', {
        'analysis_req': analysis_req
    })


@login_required
def scenario_chat_view(request, analysis_request_id):
    """
    Многошаговый диалог с ChatGPT, храним переписку в chat_history (JSON).
    """
    analysis_req = get_object_or_404(AnalysisRequest, id=analysis_request_id, user=request.user)
    if request.method == 'POST':
        user_message = request.POST.get('user_message', '').strip()
        if user_message:
            # Добавляем сообщение пользователя в историю чата
            chat_history = analysis_req.chat_history
            chat_history.append({"role": "user", "content": user_message})

            # Вызываем ChatGPT
            response_text = chatgpt_conversation(chat_history)
            # Добавляем ответ от ChatGPT в историю
            chat_history.append({"role": "assistant", "content": response_text})

            analysis_req.chat_history = chat_history
            analysis_req.save()

    return render(request, 'analysis/scenario_chat.html', {
        'analysis_req': analysis_req
    })
