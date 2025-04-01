from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.view_files, name='view_files'),
    path('download/', views.download_file, name='download_file'),
    path('download_multiple/', views.download_multiple, name='download_multiple'),
    path('oauth/start/', views.start_auth, name='start_auth'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
]