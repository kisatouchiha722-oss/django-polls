from django.urls import path
from . import views

from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    # Твои старые маршруты опросов
    path('', views.index, name='index'),
    path('<int:poll_id>/', views.detail, name='detail'),
    path('<int:poll_id>/vote/', views.vote, name='vote'),
    path('<int:poll_id>/results/', views.results, name='results'),

    # Твои маршруты ИИ-ассистента
    path('assistant/', views.ai_assistant, name='ai_assistant'),
    path('api/chat/', views.ai_chat_api, name='api_chat_api'),

    # --- НОВЫЕ МАРШРУТЫ ДЛЯ ТРЕБОВАНИЙ ПРЕПОДАВАТЕЛЯ ---
    # Пути для подсистемы авторизации
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Путь для отправки отзывов (обратная связь)
    path('<int:poll_id>/feedback/', views.add_feedback, name='add_feedback'),
]