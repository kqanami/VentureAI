from django.urls import path
from .views import (
    create_analysis_request_view,
    analysis_detail_view,
    scenario_chat_view
)

urlpatterns = [
    path('project/<int:project_id>/create/', create_analysis_request_view, name='create_analysis'),
    path('detail/<int:analysis_request_id>/', analysis_detail_view, name='analysis_detail'),
    path('scenario-chat/<int:analysis_request_id>/', scenario_chat_view, name='scenario_chat'),
]
