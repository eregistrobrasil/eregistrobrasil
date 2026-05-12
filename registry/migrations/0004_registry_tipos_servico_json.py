from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0003_rename_registry_tipo_servico_idx_registry_re_tipo_se_de0d0c_idx_and_more'),
    ]

    operations = [
        # Remove índices que referenciam o campo tipo_servico
        migrations.RemoveIndex(
            model_name='registry',
            name='registry_re_tipo_se_de0d0c_idx',
        ),
        migrations.RemoveIndex(
            model_name='registry',
            name='registry_re_estado_f0a897_idx',
        ),
        # Troca o campo CharField por JSONField
        migrations.RemoveField(
            model_name='registry',
            name='tipo_servico',
        ),
        migrations.AddField(
            model_name='registry',
            name='tipo_servico',
            field=models.JSONField(
                default=list,
                verbose_name='Tipos de Serviço',
                help_text='Lista de tipos: civil, notas, imoveis, protesto',
            ),
        ),
        # Índice simples em ativo
        migrations.AddIndex(
            model_name='registry',
            index=models.Index(fields=['ativo'], name='registry_re_ativo_idx'),
        ),
    ]
