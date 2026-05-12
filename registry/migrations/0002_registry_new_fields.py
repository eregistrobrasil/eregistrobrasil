from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registry',
            name='tipo_servico',
            field=models.CharField(
                choices=[
                    ('civil', 'Civil'),
                    ('notas', 'Notas'),
                    ('imoveis', 'Imóveis'),
                    ('protesto', 'Protesto'),
                ],
                default='civil',
                max_length=20,
                verbose_name='Tipo de Serviço',
            ),
        ),
        migrations.AddField(
            model_name='registry',
            name='cnpj',
            field=models.CharField(blank=True, max_length=18, verbose_name='CNPJ'),
        ),
        migrations.AddField(
            model_name='registry',
            name='endereco',
            field=models.CharField(blank=True, max_length=300, verbose_name='Endereço'),
        ),
        migrations.AddField(
            model_name='registry',
            name='telefone',
            field=models.CharField(blank=True, max_length=20, verbose_name='Telefone'),
        ),
        migrations.AlterUniqueTogether(
            name='registry',
            unique_together={('nome', 'estado', 'cidade')},
        ),
        migrations.AddIndex(
            model_name='registry',
            index=models.Index(fields=['tipo_servico'], name='registry_tipo_servico_idx'),
        ),
        migrations.AddIndex(
            model_name='registry',
            index=models.Index(fields=['estado', 'cidade', 'tipo_servico'], name='registry_estado_cidade_tipo_idx'),
        ),
    ]
