from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserRegistrationForm(forms.ModelForm):
    """
    Форма для регистрации нового пользователя
    """
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают!")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # При регистрации делаем is_active=False, чтобы ждать активации по email
        user.is_active = False
        if commit:
            user.save()
        return user

