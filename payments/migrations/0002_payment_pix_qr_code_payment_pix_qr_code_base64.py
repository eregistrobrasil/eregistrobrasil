from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='pix_qr_code',
            field=models.TextField(blank=True, verbose_name='PIX Copia e Cola'),
        ),
        migrations.AddField(
            model_name='payment',
            name='pix_qr_code_base64',
            field=models.TextField(blank=True, verbose_name='PIX QR Code (base64)'),
        ),
    ]
