# Generated by Django 3.2.3 on 2024-08-27 20:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="recipe",
            options={
                "ordering": ["-pub_date"],
                "verbose_name": "Рецепт",
                "verbose_name_plural": "Рецепты",
            },
        ),
    ]