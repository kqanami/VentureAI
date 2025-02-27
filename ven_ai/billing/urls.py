from django.urls import path
from .views import buy_tokens_view, billing_history_view

urlpatterns = [
    path('buy/', buy_tokens_view, name='buy_tokens'),
    path('history/', billing_history_view, name='billing_history'),
]
