from django import forms

PACKAGE_CHOICES = (
    ('10', '10 токенов за 1000 тенге.'),
    ('20', '20 токенов за 1800 тенге.'),
    ('50', '50 токенов за 4000 тенге.'),
)

class BuyTokensForm(forms.Form):
    package = forms.ChoiceField(
        choices=PACKAGE_CHOICES,
        widget=forms.RadioSelect,
        label='Выберите пакет'
    )
