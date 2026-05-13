from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0019_servicestateprice_observacao_servicestateprice_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_system_service',
            field=models.BooleanField(
                default=False,
                help_text='Serviços marcados pelo seed. Não pode ser criado/excluído manualmente.',
                verbose_name='Serviço do Sistema',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='has_fixed_price',
            field=models.BooleanField(
                default=False,
                help_text='Quando ativo, o preço é fixo (R$ 49,90 para Federais e Estaduais) independente do estado.',
                verbose_name='Preço Fixo Global',
            ),
        ),
    ]
