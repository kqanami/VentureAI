from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import landing_page
from . import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('billing/', include('billing.urls')),
    path('analysis/', include('analysis.urls')),
    path('', landing_page, name='landing'),
    path('crm/', views.crm_dashboard, name='crm_dashboard'),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)