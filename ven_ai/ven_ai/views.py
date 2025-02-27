from django.shortcuts import render
from django.utils import timezone

def landing_page(request):
    # Вы можете передать сюда дополнительные данные, если потребуется
    return render(request, 'landing.html', {
        'now': timezone.now()
    })

