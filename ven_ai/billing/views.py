from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BuyTokensForm
from .models import Transaction

@login_required
def buy_tokens_view(request):
    """
    Покупка токенов без реальной интеграции с платежками.
    Просто выбор пакета, добавляем токены и создаём запись Transaction.
    """
    if request.method == 'POST':
        form = BuyTokensForm(request.POST)
        if form.is_valid():
            package = form.cleaned_data['package']
            if package == '10':
                tokens_amount = 10
                price = 1000
            elif package == '20':
                tokens_amount = 20
                price = 1800
            elif package == '50':
                tokens_amount = 50
                price = 4000
            else:
                # непредвиденный вариант, можно кинуть ошибку или вернуть
                tokens_amount = 0
                price = 0

            # Добавляем токены пользователю
            request.user.tokens += tokens_amount
            request.user.save()

            # Записываем транзакцию
            Transaction.objects.create(
                user=request.user,
                tokens_purchased=tokens_amount,
                amount_paid=price
            )

            messages.success(request, f"Вы купили {tokens_amount} токенов за {price} тенге.")
            return redirect('billing_history')
    else:
        form = BuyTokensForm()

    return render(request, 'billing/buy_tokens.html', {
        'form': form
    })


@login_required
def billing_history_view(request):
    """
    Список всех транзакций текущего пользователя.
    """
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'billing/billing_history.html', {
        'transactions': transactions
    })
