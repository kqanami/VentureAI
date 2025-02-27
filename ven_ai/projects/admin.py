from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'budget', 'location', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('name', 'description')
