from django.db import migrations

HIDDEN_SLUGS = ['pesquisa', 'traducao-e-apostilamento', 'protesto']


def hide_nav_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(slug__in=HIDDEN_SLUGS).update(show_in_nav=False)


def show_nav_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(slug__in=HIDDEN_SLUGS).update(show_in_nav=True)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0023_category_show_in_nav'),
    ]

    operations = [
        migrations.RunPython(hide_nav_categories, reverse_code=show_nav_categories),
    ]
