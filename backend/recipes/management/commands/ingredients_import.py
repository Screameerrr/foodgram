import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = "Import data from CSV file to Ingredients model"

    def handle(self, *args, **options):
        # Исправленный путь к файлу ingredients.csv
        ingredients = os.path.join('/app', 'data', 'ingredients.csv')  # Явно указываем путь в контейнере

        # Вывод пути для отладки
        self.stdout.write(self.style.WARNING(f"Путь к файлу: {ingredients}"))

        try:
            with open(ingredients, encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=row[0], defaults={"measurement_unit": row[1]}
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Добавлен ингредиент {row[0]}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Ингредиент {row[0]} уже существует.")
                        )

            self.stdout.write(self.style.SUCCESS("Импорт завершен."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("Файл ingredients.csv не найден. Проверьте путь."))


