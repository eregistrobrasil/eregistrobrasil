from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Permissao, Role, UserPermission


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('tipo', 'cpf', 'phone', 'birth_date')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)


@admin.register(Permissao)
class PermissaoAdmin(admin.ModelAdmin):
    list_display = ('codename', 'nome', 'modulo')
    list_filter = ('modulo',)
    search_fields = ('codename', 'nome')
    ordering = ('modulo', 'codename')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'criado_em')
    filter_horizontal = ('permissoes',)
    search_fields = ('nome',)


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'criado_em')
    filter_horizontal = ('roles', 'permissoes_extras', 'permissoes_negadas')
    search_fields = ('user__email', 'user__first_name')
    raw_id_fields = ('user',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
