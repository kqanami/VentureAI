from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, BusinessProject

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class BusinessProjectForm(forms.ModelForm):
    class Meta:
        model = BusinessProject
        fields = ['name', 'description', 'budget','location', 'competition_level']
