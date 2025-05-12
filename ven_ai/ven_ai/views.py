from django.shortcuts import render
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone
import random

def landing_page(request):

    return render(request, 'landing.html', {
        'now': timezone.now()
    })

def crm_dashboard(request):
    total_users = (328)
    active_users = random.randint(10, 15)
    analyses_done = (712)

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'analyses_done': analyses_done,
    }
    return render(request, 'crm/dashboard.html', context)