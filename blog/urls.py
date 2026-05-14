from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='list'),
    path('categoria/<slug:slug>/', views.CategoryListView.as_view(), name='category'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='detail'),
]

