from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0029_update_preco_testamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='canal_oficial',
            field=models.CharField(
                blank=True,
                help_text=(
                    'Nome do canal oficial onde o interessado pode solicitar o documento '
                    'diretamente, sem intermediação. Ex: CENSEC/e-notariado, Registro Civil '
                    'Nacional (registrocivil.org.br). Exibido no aviso de transparência da '
                    'página do serviço; em branco, usa o texto genérico.'
                ),
                max_length=200,
                verbose_name='Canal Oficial Direto',
            ),
        ),
    ]
