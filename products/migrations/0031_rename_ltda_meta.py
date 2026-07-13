import re

from django.db import migrations

PATTERN = re.compile(r'E-Registro Brasil(?! LTDA)')


def add_ltda(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        updated = []
        for field in ('meta_title', 'meta_description'):
            value = getattr(product, field) or ''
            new_value = PATTERN.sub('E-Registro Brasil LTDA', value)
            if new_value != value:
                setattr(product, field, new_value)
                updated.append(field)
        if updated:
            product.save(update_fields=updated)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0030_product_canal_oficial'),
    ]

    operations = [
        migrations.RunPython(add_ltda, migrations.RunPython.noop),
    ]
