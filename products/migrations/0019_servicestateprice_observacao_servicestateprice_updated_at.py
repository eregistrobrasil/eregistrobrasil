from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_product_tipo_cartorio'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicestateprice',
            name='observacao',
            field=models.TextField(blank=True, verbose_name='Observação Interna'),
        ),
        migrations.AddField(
            model_name='servicestateprice',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizado em'),
        ),
    ]
