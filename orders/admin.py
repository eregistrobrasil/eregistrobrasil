from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity', 'get_total')
    fields = ('product_name', 'price', 'quantity', 'requester_name', 'requester_document')

    def get_total(self, obj):
        return f'R$ {obj.get_total():.2f}'
    get_total.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'customer_name', 'customer_email', 'total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'customer_cpf', 'payment_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_editable = ('status',)
    inlines = (OrderItemInline,)
    fieldsets = (
        ('Identificação', {'fields': ('id', 'status', 'user')}),
        ('Cliente', {'fields': ('customer_name', 'customer_email', 'customer_cpf', 'customer_phone')}),
        ('Financeiro', {'fields': ('subtotal', 'total', 'payment_id', 'payment_method')}),
        ('Extras', {'fields': ('notes', 'created_at', 'updated_at')}),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'created_at', 'updated_at')
    readonly_fields = ('session_key', 'created_at', 'updated_at')
