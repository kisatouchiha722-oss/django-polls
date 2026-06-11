from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Добавь этот импорт
from django.conf.urls.static import static # И этот импорт

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('polls.urls')),
]

# И добавь этот блок в самый конец файла:
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
