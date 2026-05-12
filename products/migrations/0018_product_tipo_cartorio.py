from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0017_seed_preco_penhor_safra'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='tipo_cartorio',
            field=models.CharField(
                blank=True,
                choices=[
                    ('civil', 'Civil'),
                    ('notas', 'Notas'),
                    ('imoveis', 'Imóveis'),
                    ('protesto', 'Protesto'),
                ],
                help_text='Define qual tipo de cartório é utilizado neste serviço.',
                max_length=20,
                verbose_name='Tipo de Cartório',
            ),
        ),
    ]
