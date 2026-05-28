# Generated migration — adição de campos de controle de senha automática

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_userprofile_tipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='senha_gerada_automaticamente',
            field=models.BooleanField(default=False, verbose_name='Senha gerada automaticamente'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='senha_alterada_pelo_usuario',
            field=models.BooleanField(default=False, verbose_name='Senha alterada pelo usuário'),
        ),
    ]
