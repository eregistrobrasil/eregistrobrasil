from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pagar/<uuid:order_id>/', views.CreatePaymentView.as_view(), name='create'),
    path('sucesso/<uuid:order_id>/', views.PaymentSuccessView.as_view(), name='success'),
    path('falha/<uuid:order_id>/', views.PaymentFailureView.as_view(), name='failure'),
    path('pendente/<uuid:order_id>/', views.PaymentPendingView.as_view(), name='pending'),
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
]
