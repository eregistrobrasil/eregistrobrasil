from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_seed_imoveis_services'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='show_in_nav',
            field=models.BooleanField(default=True, verbose_name='Exibir na Navegação'),
        ),
    ]
