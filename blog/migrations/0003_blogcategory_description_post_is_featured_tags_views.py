from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_post_meta_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogcategory',
            name='description',
            field=models.TextField(blank=True, verbose_name='Descrição'),
        ),
        migrations.AddField(
            model_name='post',
            name='is_featured',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Destaque'),
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.CharField(
                blank=True,
                help_text='Separe com vírgulas (ex: certidão, imóvel, registro)',
                max_length=500,
                verbose_name='Tags',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='views_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Visualizações'),
        ),
    ]
