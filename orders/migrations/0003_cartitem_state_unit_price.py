from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_orderstatuslog_order_cartorio_order_cidade_and_more'),
        ('products', '0004_alter_servicestateprice_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='state',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='products.state',
                verbose_name='Estado',
            ),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='unit_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Preço Unitário',
            ),
        ),
    ]
