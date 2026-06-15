from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0026_certidao_negativa_testamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='imagem_static',
            field=models.CharField(
                blank=True,
                help_text='Caminho relativo ao diretório static/. Ex: img/servicos/certidao-nascimento.webp',
                max_length=200,
                verbose_name='Imagem do Serviço',
            ),
        ),
    ]
