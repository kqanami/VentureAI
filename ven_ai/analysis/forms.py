from django import forms
from projects.models import Project

class AnalysisForm(forms.Form):
    budget = forms.FloatField(label="Бюджет (тг.)", initial=100000)
    competition = forms.FloatField(label="Уровень конкуренции", initial=1.0)
    location_factor = forms.FloatField(label="Фактор локации (0..1)", initial=0.5)
    marketing_skill = forms.FloatField(label="Навык маркетинга (0..1)", initial=0.5)
    team_experience = forms.FloatField(label="Опыт команды (0..1)", initial=0.5)
    latitude = forms.FloatField(label="Широта")
    longitude = forms.FloatField(label="Долгота")

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            # Если передали конкретный объект Project, берём из него координаты
            self.fields['latitude'].initial = project.latitude
            self.fields['longitude'].initial = project.longitude
