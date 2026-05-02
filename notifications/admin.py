from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'usuario', 'mensagem', 'lida', 'data')
    list_filter = ('tipo', 'lida', 'data')
    search_fields = ('usuario__email', 'mensagem')
    list_editable = ('lida',)
    readonly_fields = ('data',)
