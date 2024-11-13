import logging
import os
from csv import reader

from django.core.management.base import BaseCommand

from foodgram.settings import CSV_FILES_DIR
from recipes.models import Ingredient, Tag

logging.basicConfig(
    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

def load(csv_file, model, *fields):
    """Загружает данные из CSV-файла в указанную модель."""

    if model.objects.exists():
        logging.info(f'В таблице {model._meta.db_table} уже есть данные.')
        return

    file_path = os.path.join(CSV_FILES_DIR, csv_file)
    if not os.path.exists(file_path):
        logging.error(f'Файл {csv_file} не найден в директории {CSV_FILES_DIR}.')
        return

    with open(file_path, encoding='utf-8') as rows:
        logging.info(f'Начинаю загрузку {csv_file} в {model._meta.db_table}')
        try:
            for row in reader(rows):
                model.objects.create(**dict(zip(fields, row)))
            logging.info(f'Данные из {csv_file} успешно загружены.')
        except Exception as error:
            logging.error(f'Ошибка {error}! Проверьте строку {row} в файле {csv_file}')

class Command(BaseCommand):
    help = 'Загружает данные из CSV-файлов в модели.'

    def handle(self, *args, **options):
        models = [
            ('tags.csv', Tag, 'name', 'slug'),
            ('ingredients.csv', Ingredient, 'name', 'measurement_unit'),
        ]

        for item in models:
            load(*item)
