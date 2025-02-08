# core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('project/create/', views.project_create, name='project_create'),
    path('project/<int:pk>/edit/', views.project_update, name='project_update'),
    path('project/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('project/<int:pk>/analyze/', views.project_analyze, name='project_analyze'),
    path('buy-tokens/', views.buy_tokens, name='buy_tokens'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('project/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('similar-businesses/', views.similar_businesses, name='similar_businesses'),
    path('business-advice/', views.business_advice, name='business_advice'),
]
