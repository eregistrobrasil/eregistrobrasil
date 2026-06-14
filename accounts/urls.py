from django.urls import path
from django.contrib.auth.views import (
    LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from . import views
from . import views_permissions

app_name = 'accounts'

urlpatterns = [
    path('cadastro/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('perfil/', views.ProfileUpdateView.as_view(), name='profile'),
    path('alterar-senha/', views.ChangePasswordView.as_view(), name='change_password'),

    # Gestão de permissões
    path('permissoes/', views_permissions.PermissaoListView.as_view(), name='permissions_list'),
    path('permissoes/usuarios/', views_permissions.UsersListView.as_view(), name='users_list'),
    path('permissoes/roles/criar/', views_permissions.RoleCreateView.as_view(), name='role_create'),
    path('permissoes/roles/<int:pk>/editar/', views_permissions.RoleEditView.as_view(), name='role_edit'),
    path('permissoes/roles/<int:pk>/excluir/', views_permissions.RoleDeleteView.as_view(), name='role_delete'),
    path('permissoes/usuario/<int:user_id>/', views_permissions.UserPermissionView.as_view(), name='user_permissions'),
    path('permissoes/usuarios/criar/', views_permissions.UserCreateView.as_view(), name='user_create'),

    # Password reset
    path('senha/recuperar/', PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/conta/senha/recuperar/enviado/',
    ), name='password_reset'),
    path('senha/recuperar/enviado/', PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('senha/redefinir/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/conta/senha/redefinida/',
    ), name='password_reset_confirm'),
    path('senha/redefinida/', PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
]
