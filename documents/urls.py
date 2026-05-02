from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload/<uuid:order_pk>/', views.DocumentUploadView.as_view(), name='upload'),
    path('excluir/<int:pk>/', views.DocumentDeleteView.as_view(), name='delete'),
]
