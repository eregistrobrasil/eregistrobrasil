import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_tiposervico_product_tipo'),
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=2, unique=True, verbose_name='Sigla')),
                ('name', models.CharField(max_length=50, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estados',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ServiceStatePrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço')),
                ('promotional_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço Promocional')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='state_prices',
                    to='products.product',
                    verbose_name='Serviço',
                )),
                ('state', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='service_prices',
                    to='products.state',
                    verbose_name='Estado',
                )),
            ],
            options={
                'verbose_name': 'Preço por Estado',
                'verbose_name_plural': 'Preços por Estado',
            },
        ),
        migrations.AddIndex(
            model_name='servicestateprice',
            index=models.Index(fields=['service', 'state'], name='products_se_service_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='servicestateprice',
            unique_together={('service', 'state')},
        ),
    ]
