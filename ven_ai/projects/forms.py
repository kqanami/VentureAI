from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'budget', 'location', 'latitude','longitude',)  # file_upload и т.д. если нужно
        # widgets = {
        #     'description': forms.Textarea(attrs={'rows': 4}),
        # }
