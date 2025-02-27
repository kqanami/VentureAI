from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tokens_purchased', 'amount_paid', 'created_at')
    list_filter = ('created_at', 'tokens_purchased')
    search_fields = ('user__username',)
