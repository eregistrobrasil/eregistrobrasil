def cart_processor(request):
    cart_count = 0
    if hasattr(request, 'session'):
        session_key = request.session.session_key
        if session_key:
            from orders.models import Cart
            try:
                cart = Cart.objects.get(session_key=session_key)
                cart_count = cart.get_count()
            except Cart.DoesNotExist:
                pass
    return {'cart_count': cart_count}
