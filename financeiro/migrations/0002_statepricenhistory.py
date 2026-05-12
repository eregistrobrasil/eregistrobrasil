from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('products', '0019_servicestateprice_observacao_servicestateprice_updated_at'),
        ('financeiro', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatePriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state_code', models.CharField(db_index=True, max_length=2, verbose_name='Estado (sigla)')),
                ('preco_anterior', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço Anterior')),
                ('preco_novo', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço Novo')),
                ('observacao', models.TextField(blank=True, verbose_name='Observação')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('alterado_por', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='auth.user', verbose_name='Alterado por'
                )),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='state_price_history', to='products.product',
                    verbose_name='Serviço'
                )),
                ('service_state_price', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='history', to='products.servicestateprice',
                    verbose_name='Registro de Preço'
                )),
            ],
            options={
                'verbose_name': 'Histórico de Preço por Estado',
                'verbose_name_plural': 'Histórico de Preços por Estado',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='statepricehistory',
            index=models.Index(fields=['service', 'state_code'], name='fin_sph_service_state_idx'),
        ),
        migrations.AddIndex(
            model_name='statepricehistory',
            index=models.Index(fields=['-created_at'], name='fin_sph_created_idx'),
        ),
    ]
