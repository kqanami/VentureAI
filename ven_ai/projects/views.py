from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Project
from .forms import ProjectForm

@login_required
def project_list(request):
    """
    Список проектов текущего пользователя.
    Дополнительно: поиск, сортировка и т.д.
    """
    # Берём все проекты, где owner = request.user
    projects = Project.objects.filter(owner=request.user)

    # Дополнительный фильтр по названию (поиск)
    search_query = request.GET.get('q')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )


    sort_by_budget = request.GET.get('sort_by_budget')
    if sort_by_budget == 'asc':
        projects = projects.order_by('budget')
    elif sort_by_budget == 'desc':
        projects = projects.order_by('-budget')

    return render(request, 'projects/project_list.html', {
        'projects': projects,
    })


@login_required
def project_detail(request, pk):
    """
    Детальная страница проекта.
    Убедимся, что владелец = request.user
    """
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(request, 'projects/project_detail.html', {
        'project': project,
    })


@login_required
def project_create(request):
    """
    Создание нового проекта.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            proj = form.save(commit=False)
            proj.owner = request.user
            proj.save()
            messages.success(request, "Проект успешно создан!")
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_create.html', {
        'form': form,
    })


@login_required
def project_update(request, pk):
    """
    Редактирование проекта.
    Проверяем, что текущий пользователь = владелец.
    """
    project = get_object_or_404(Project, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Проект обновлён!")
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_update.html', {
        'form': form,
        'project': project,
    })


@login_required
def project_delete(request, pk):
    """
    Удаление проекта.
    Проверяем владельца.
    """
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Проект удалён!")
        return redirect('project_list')
    return render(request, 'projects/project_delete.html', {
        'project': project,
    })
