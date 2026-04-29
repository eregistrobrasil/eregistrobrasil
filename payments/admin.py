from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'amount', 'payment_method', 'mercadopago_id', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order__customer_email', 'mercadopago_id', 'preference_id')
    readonly_fields = ('created_at', 'updated_at', 'raw_response')
