from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_servicestateprice_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrecoImovelEstado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_certidao', models.CharField(
                    db_index=True,
                    help_text='Ex: matricula, inteiro_teor, vintenaria, ...',
                    max_length=50,
                    verbose_name='Tipo de Certidão',
                )),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('state', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='imovel_prices',
                    to='products.state',
                    verbose_name='Estado',
                )),
            ],
            options={
                'verbose_name': 'Preço Imóvel por Estado',
                'verbose_name_plural': 'Preços Imóvel por Estado',
                'ordering': ['tipo_certidao', 'state__name'],
            },
        ),
        migrations.AddConstraint(
            model_name='precoimovelestado',
            constraint=models.UniqueConstraint(
                fields=['tipo_certidao', 'state'],
                name='unique_tipo_certidao_state',
            ),
        ),
        migrations.AddIndex(
            model_name='precoimovelestado',
            index=models.Index(fields=['tipo_certidao', 'state'], name='products_pr_tipo_ce_idx'),
        ),
    ]
