def categories_processor(request):
    from products.models import Category
    return {'all_categories': Category.objects.filter(is_active=True, show_in_nav=True)}
