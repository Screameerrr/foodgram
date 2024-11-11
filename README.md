# Foodgram

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

2. Настройте Docker:
   
 ```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

3. Создайте файл .env и укажите переменные окружения по примеру .env.example:
   
 ```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

4.Запустите проект с помощью Docker Compose:

```
docker-compose up --build
```

5. Выполните миграции базы данных и соберите статику:

```
docker-compose exec python manage.py migrate
docker-compose exec python manage.py collectstatic --noinput
```

6. Создайте суперпользователя:

```
docker-compose exec web python manage.py createsuperuser
```

7. Проект будет доступен по адресу: http://localhost



##Запуск на сервере

1. Настройка окружения:
   
- Настройте переменные в файле .env и используйте docker-compose.production.yml.

2. Установите и настройте Nginx:

```
sudo apt install nginx -y
sudo systemctl start nginx
```

3. Настройте файервол и разрешите доступ:

```
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

4.  Настройка Nginx: Откройте файл конфигурации Nginx и измените настройки:

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
Проверьте корректность настроек:

```
sudo nginx -t
sudo systemctl restart nginx
```


5.  Загрузите образы из DockerHub и запустите контейнеры:

```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml up -d
```

6.  Выполните миграции, соберите статику и загрузите данные:

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_data
sudo docker compose -f docker-compose.production.yml exec backend python manage.py demo_data
```


## Спецификация API


Пользователи:

/api/users/ (GET/POST) — Список пользователей и регистрация
/api/users/me/ (GET) — Текущий пользователь
/api/users/set_password/ (POST) — Изменение пароля
/api/auth/token/login/ (POST) — Получить токен авторизации
/api/auth/token/logout/ (POST) — Удаление токена


Рецепты:

/api/recipes/ (GET/POST) — Список рецептов и создание
/api/recipes/{id}/ (GET/PATCH/DELETE) — Работа с отдельным рецептом
/api/recipes/{id}/favorite/ (POST/DELETE) — Добавить/удалить рецепт из избранного
/api/recipes/{id}/shopping_cart/ (POST/DELETE) — Добавить/удалить рецепт из списка покупок


Теги и ингредиенты:

/api/tags/ (GET) — Список тегов
/api/ingredients/ (GET) — Список ингредиентов с возможностью поиска


Автор проекта: Максим Шевчук
