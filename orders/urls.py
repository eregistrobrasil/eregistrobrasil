from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('carrinho/', views.CartView.as_view(), name='cart'),
    path('carrinho/adicionar/<slug:slug>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('carrinho/remover/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('carrinho/atualizar/<int:item_id>/', views.UpdateCartView.as_view(), name='update_cart'),
    path('finalizar/', views.CheckoutView.as_view(), name='checkout'),
    path('meus-pedidos/', views.OrderListView.as_view(), name='order_list'),
    path('pedido/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]
