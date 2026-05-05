from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('products', '0002_tiposervico_product_tipo'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preco_anterior', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço Anterior')),
                ('preco_novo', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço Novo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('alterado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user', verbose_name='Alterado por')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='products.product', verbose_name='Serviço')),
            ],
            options={
                'verbose_name': 'Histórico de Preço',
                'verbose_name_plural': 'Histórico de Preços',
                'ordering': ['-created_at'],
            },
        ),
    ]
