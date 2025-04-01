import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, FileResponse
from urllib.parse import urlencode
from .forms import PublicLinkForm
from typing import List, Dict, Any
import zipfile
from io import BytesIO
from django.core.cache import cache
import os

# Настройки для API 
YANDEX_API_BASE_URL = 'https://cloud-api.yandex.net/v1/disk/public/resources'
YANDEX_AUTH_URL = 'https://oauth.yandex.ru/authorize'
YANDEX_TOKEN_URL = 'https://oauth.yandex.ru/token'
CLIENT_ID = settings.YANDEX_CLIENT_ID
CLIENT_SECRET = settings.YANDEX_CLIENT_SECRET
REDIRECT_URI = settings.YANDEX_REDIRECT_URI

def start_auth(request):
    """
    Перенаправляет пользователя на страницу авторизации
    """
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
    }
    auth_url = f"{YANDEX_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)

def oauth_callback(request):
    """
    Обрабатывает ответ от сервера авторизации Яндекса и сохраняет access token в сессии.
    """
    code = request.GET.get('code')
    if code:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
        }
        response = requests.post(YANDEX_TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get('access_token')
        if access_token:
            request.session['yandex_token'] = access_token
            return redirect('index')
        else:
            return HttpResponse("Ошибка получения access token.", status=400)
    else:
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        return HttpResponse(f"Ошибка авторизации: {error} - {error_description}", status=400)

def get_yandex_disk_files(public_key: str) -> List[Dict[str, Any]]:
    """
    Получает список файлов с публичного Яндекс Диска и кэширует результат на 5 минут.
    """
    cache_key = f'yandex_disk_files_{public_key}'
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    params = {'public_key': public_key, 'limit': 1000}
    response = requests.get(YANDEX_API_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json().get('_embedded', {}).get('items', [])

    cache.set(cache_key, data, 60 * 5)  # Кэшируем на 5 минут
    return data

def index(request):
    """
    Отображает страницу с формой для ввода публичной ссылки.
    """
    form = PublicLinkForm()
    return render(request, 'index.html', {'form': form})

def view_files(request):
    """
    Отображает список файлов по введённой публичной ссылке с возможностью фильтрации по типу файла.
    """
    if request.method == 'POST':
        form = PublicLinkForm(request.POST)
        if form.is_valid():
            public_key = form.cleaned_data['public_key']
            files = get_yandex_disk_files(public_key)
            file_type_filter = request.GET.get('file_type', 'all')

            if file_type_filter != 'all':
                files = [f for f in files if f['type'] == file_type_filter]

            return render(request, 'file_list.html', {'files': files, 'public_key': public_key})
        else:
            return render(request, 'index.html', {'form': form, 'error': 'Пожалуйста, введите корректную ссылку.'})
    else:
        public_key = request.GET.get('public_key')
        if public_key:
            files = get_yandex_disk_files(public_key)
            file_type_filter = request.GET.get('file_type', 'all')

            if file_type_filter != 'all':
                files = [f for f in files if f['type'] == file_type_filter]

            return render(request, 'file_list.html', {'files': files, 'public_key': public_key})
        else:
            return redirect('index')

def download_file(request):
    """
    Загружает выбранный файл с Яндекс.Диска и отправляет его пользователю.
    """
    if request.method == 'GET':
        public_key = request.GET.get('public_key')
        file_path = request.GET.get('path')
        file_name = file_path.split('/')[-1]

        download_url_params = {'public_key': public_key, 'path': file_path}
        download_url_endpoint = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'

        try:
            download_url_response = requests.get(download_url_endpoint, params=download_url_params)
            download_url_response.raise_for_status()
            download_url_data = download_url_response.json()
            download_href = download_url_data.get('href')

            if download_href:
                file_response = requests.get(download_href, stream=True)
                file_response.raise_for_status()

                response = HttpResponse(file_response.content)
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
            else:
                return HttpResponse("Не удалось получить ссылку на скачивание.", status=500)

        except requests.exceptions.RequestException as e:
            return HttpResponse(f"Ошибка при скачивании файла: {e}", status=500)
    else:
        return HttpResponse("Недопустимый метод запроса.", status=405)

def download_multiple(request):
    """
    Загружает несколько выбранных файлов, архивирует их и отправляет архив пользователю.
    """
    if request.method == 'POST':
        public_key = request.POST.get('public_key')
        selected_files = request.POST.getlist('selected_files')

        if not selected_files:
            return redirect(request.META.get('HTTP_REFERER', 'index'))

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in selected_files:
                download_url_params = {'public_key': public_key, 'path': file_path}
                download_url_endpoint = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'
                try:
                    download_url_response = requests.get(download_url_endpoint, params=download_url_params)
                    download_url_response.raise_for_status()
                    download_url_data = download_url_response.json()
                    download_href = download_url_data.get('href')

                    if download_href:
                        file_response = requests.get(download_href, stream=True)
                        file_response.raise_for_status()
                        file_name = file_path.split('/')[-1]
                        # Добавляем файл в архив
                        zf.writestr(file_name, file_response.content)
                    else:
                        print(f"Не удалось получить ссылку на скачивание для: {file_path}")
                except requests.exceptions.RequestException as e:
                    print(f"Ошибка при скачивании {file_path}: {e}")

        response = FileResponse(
            zip_buffer.getvalue(),
            as_attachment=True,
            filename='selected_files.zip',
            content_type='application/zip'
        )
        return response
    else:
        return HttpResponse("Недопустимый метод запроса.", status=405)
