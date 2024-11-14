# Foodgram

[![GitHub Actions Status](https://github.com/Screameerrr/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Screameerrr/foodgram/actions)

Foodgram — это онлайн-сервис для публикации рецептов, планирования покупок и обмена идеями по приготовлению блюд. Авторизованные пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное, подписываться на других пользователей и скачивать список покупок с ингредиентами для выбранных блюд.

## Возможности проекта

- **Публикация рецептов**: Возможность добавлять, обновлять и удалять собственные рецепты с указанием ингредиентов, описанием и изображением.
- **Избранное**: Добавление рецептов в избранное для быстрого доступа.
- **Подписки**: Возможность подписываться на других пользователей и получать обновления их рецептов.
- **Список покупок**: Формирование списка ингредиентов для выбранных рецептов с возможностью скачивания в формате PDF/CSV/TXT.
- **Аутентификация и регистрация**: Поддержка токен-авторизации, регистрация и управление профилем.

---

## Стек технологий

- **Backend**: Python, Django, Django REST Framework
- **Frontend**: React
- **База данных**: PostgreSQL
- **Виртуализация**: Docker, Docker Compose
- **Веб-сервер и WSGI**: Nginx, Gunicorn
- **Автоматизация**: GitHub Actions (Workflow)

---

## Как запустить проект

### Запуск локально

1. **Клонируйте репозиторий и перейдите в директорию проекта**:
   
```
git clone https://github.com/Screameerrr/foodgram.git
cd foodgram
```

2. **Настройте Docker**:
   
 ```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

3. **Создайте файл .env и укажите переменные окружения по примеру .env.example**:
   
 ```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,your_IP, Your_domain_name
```

4.**Запустите проект с помощью Docker Compose**:

```
docker-compose up --build
```

5. **Выполните миграции базы данных и соберите статику**:

```
docker-compose exec python manage.py migrate
docker-compose exec python manage.py collectstatic --noinput
```

6. **Создайте суперпользователя**:

```
docker-compose exec python manage.py createsuperuser
```

7. **Проект будет доступен по адресу**: http://localhost

## Загрузка данных ингредиентов и тегов из CSV-файлов

### Для автоматической загрузки данных ингредиентов и тегов в базу данных вашего проекта выполните следующие шаги:

1. **Подготовьте CSV-файлы**
 
Убедитесь, что файлы ingredients.csv и tags.csv находятся в директории foodgram/backend/recipes/data.

Структура папок должна быть следующей:

```
foodgram/
├── backend/
│   ├── recipes/
│   │   ├── data/
│   │   │   ├── ingredients.csv
│   │   │   └── tags.csv
│   │   ├── management/
│   │   │   ├── commands/
│   │   │   │   └── load_data.py
│   │   │   └── __init__.py
```

2. **Проверьте настройку пути к CSV-файлам**
   
Убедитесь, что в вашем файле settings.py указана правильная переменная CSV_FILES_DIR, которая должна указывать на директорию с CSV-файлами:

```
CSV_FILES_DIR = os.path.join(BASE_DIR, 'recipes', 'data')
```
3. **Примените миграции**
   
Перед загрузкой данных необходимо создать структуру базы данных:

```
python manage.py migrate
```

4. **Запустите команду загрузки данных**
   
Выполните команду:

```
python manage.py load_data
```



### Запуск на сервере

1. **Настройка окружения**:
   
- Настройте переменные в файле .env и используйте docker-compose.production.yml.

2. **Установите и настройте Nginx**:

```
sudo apt install nginx -y
sudo systemctl start nginx
```

3. **Настройте файервол и разрешите доступ**:

```
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

4.  **Настройка Nginx: Откройте файл конфигурации Nginx и измените настройки**:

```
server {
    listen 80;
    server_name your_domain_name or IP;

    location / {
        proxy_set_header HOST $host;
        proxy_pass http://127.0.0.1:8000;
    }
}
```
- **Проверьте корректность настроек**:

```
sudo nginx -t
sudo systemctl restart nginx
```


5.  **Загрузите образы из DockerHub и запустите контейнеры**:

```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml up -d
```

6.  **Выполните миграции, соберите статику и загрузите данные**:

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_data
sudo docker compose -f docker-compose.production.yml exec backend python manage.py demo_data
```


## Спецификация API

# API Actions

**В проекте Foodgram реализованы следующие действия (ACTION) для работы с API**:

## Пользователи

| Метод | Путь                   | Описание                              |
|-------|------------------------ |---------------------------------------|
| GET   | `/api/users/`          | Получение списка всех пользователей   |
| POST  | `/api/users/`          | Регистрация нового пользователя       |
| GET   | `/api/users/{id}/`     | Получение профиля конкретного пользователя |
| GET   | `/api/users/me/`       | Получение данных текущего пользователя|
| PUT   | `/api/users/me/avatar/`| Добавление или обновление аватара     |
| DELETE| `/api/users/me/avatar/`| Удаление аватара                      |
| POST  | `/api/users/set_password/` | Изменение пароля пользователя     |
| POST  | `/api/auth/token/login/`   | Получение токена для авторизации  |
| POST  | `/api/auth/token/logout/`  | Удаление токена                    |

## Рецепты

| Метод | Путь                        | Описание                              |
|-------|----------------------------- |---------------------------------------|
| GET   | `/api/recipes/`             | Получение списка всех рецептов        |
| POST  | `/api/recipes/`             | Создание нового рецепта               |
| GET   | `/api/recipes/{id}/`        | Получение информации о рецепте        |
| PATCH | `/api/recipes/{id}/`        | Обновление рецепта (только автор)     |
| DELETE| `/api/recipes/{id}/`        | Удаление рецепта (только автор)       |
| POST  | `/api/recipes/{id}/favorite/` | Добавление рецепта в избранное     |
| DELETE| `/api/recipes/{id}/favorite/` | Удаление рецепта из избранного     |
| POST  | `/api/recipes/{id}/shopping_cart/` | Добавление рецепта в список покупок |
| DELETE| `/api/recipes/{id}/shopping_cart/` | Удаление рецепта из списка покупок |

## Теги

| Метод | Путь                  | Описание                              |
|-------|----------------------- |---------------------------------------|
| GET   | `/api/tags/`          | Получение списка всех тегов           |
| GET   | `/api/tags/{id}/`     | Получение информации о конкретном теге|

## Ингредиенты

| Метод | Путь                        | Описание                              |
|-------|----------------------------- |---------------------------------------|
| GET   | `/api/ingredients/`         | Получение списка ингредиентов         |
| GET   | `/api/ingredients/{id}/`    | Получение информации об ингредиенте   |

## Подписки

| Метод | Путь                           | Описание                              |
|-------|-------------------------------- |---------------------------------------|
| GET   | `/api/users/subscriptions/`    | Получение списка подписок текущего пользователя |
| POST  | `/api/users/{id}/subscribe/`   | Подписаться на пользователя           |
| DELETE| `/api/users/{id}/subscribe/`   | Отписаться от пользователя            |

---




**Автор проекта**: Максим Шевчук
