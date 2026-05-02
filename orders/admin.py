from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderStatusLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity', 'get_total')
    fields = ('product_name', 'price', 'quantity', 'requester_name', 'requester_document')

    def get_total(self, obj):
        return f'R$ {obj.get_total():.2f}'
    get_total.short_description = 'Total'


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ('status_anterior', 'status_novo', 'usuario', 'observacao', 'data')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'customer_name', 'tipo_certidao', 'status', 'prioridade',
                    'responsavel', 'prazo_entrega', 'esta_atrasado', 'total', 'created_at')
    list_filter = ('status', 'tipo_certidao', 'prioridade', 'estado', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'customer_cpf', 'payment_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_editable = ('status', 'prioridade', 'responsavel')
    raw_id_fields = ('responsavel', 'cartorio')
    inlines = (OrderItemInline, OrderStatusLogInline)
    fieldsets = (
        ('Identificação', {'fields': ('id', 'status', 'user', 'prioridade')}),
        ('Cliente', {'fields': ('customer_name', 'customer_email', 'customer_cpf', 'customer_phone')}),
        ('Certidão', {'fields': ('tipo_certidao', 'estado', 'cidade', 'cartorio')}),
        ('Operacional', {'fields': ('responsavel', 'prazo_entrega', 'sla_horas', 'data_envio', 'data_conclusao')}),
        ('Financeiro', {'fields': ('subtotal', 'total', 'payment_id', 'payment_method')}),
        ('Extras', {'fields': ('notes', 'created_at', 'updated_at')}),
    )

    def esta_atrasado(self, obj):
        return obj.esta_atrasado
    esta_atrasado.boolean = True
    esta_atrasado.short_description = 'Atrasado?'


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'status_anterior', 'status_novo', 'usuario', 'data')
    list_filter = ('status_novo', 'data')
    readonly_fields = ('data',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'created_at', 'updated_at')
    readonly_fields = ('session_key', 'created_at', 'updated_at')
