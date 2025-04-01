## Описание

Проект представляет собой веб-приложение, позволяющее пользователям просматривать файлы и скачивать их с общедоступных ссылок Яндекс Диска. 
Пользователь вводит публичную ссылку, после чего приложение отображает список файлов и предоставляет возможность скачивать отдельные файлы или несколько файлов в архиве.

## Cтек

* **Backend:**
    * Python
    * Django
* **Frontend:**
    * HTML
    * CSS
* **API:**
    * https://yandex.ru/dev/disk/rest/
* **Зависимости**
    * https://requests.readthedocs.io/en/latest/
    * https://pypi.org/project/python-dotenv/

## Инструкция по локальному запуску

1. 
    git clone https://github.com/cursed404/ya-disk-app.git
    cd ya-disk-app

2.  
    python -m venv venv
    source venv/bin/activate  # для Linux
    venv\Scripts\activate  # Для Windows

4.  
    pip install -r requirements.txt

5.  **Настройка переменных окружения**

    * Скопируйте файл `.env.example` в корневой директории проекта и переименуйте его в .env.
    * Откройте файл `.env` и заполните значения для переменных окружения.

        YANDEX_CLIENT_ID=
        YANDEX_CLIENT_SECRET=
        YANDEX_REDIRECT_URI=
        DJANGO_SECRET_KEY=

6.  **Выполнение миграций**

    python manage.py migrate

7.  **Запуск сервера**

    python manage.py runserver
