# Generated by Django 3.2.3 on 2024-11-22 05:41

from django.db import migrations, models
import shortener.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LinkMapped',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_hash', models.CharField(default=shortener.models.generate_hash, max_length=15, unique=True, verbose_name='Короткая ссылка')),
                ('original_url', models.URLField(max_length=256, verbose_name='Оригинальная ссылка')),
            ],
            options={
                'verbose_name': 'Ссылка',
                'verbose_name_plural': 'Ссылки',
            },
        ),
    ]
