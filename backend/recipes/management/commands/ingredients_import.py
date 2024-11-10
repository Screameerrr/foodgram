import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Import data from CSV file to Ingrediemt model"

    def handle(self, *args, **options):
        base_parent_dir = os.path.abspath(
            os.path.join(settings.BASE_DIR, os.pardir)
        )
        ingredients = os.path.join(base_parent_dir, "data", "ingredients.csv")
        with open(ingredients, encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=row[0], defaults={"measurement_unit": row[1]}
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Добавлен ингридиент {row[0]}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ингридиент {row[0]} уже существует."
                        )
                    )

        self.stdout.write(self.style.SUCCESS("Импорт завершон."))
