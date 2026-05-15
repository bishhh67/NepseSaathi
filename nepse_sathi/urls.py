from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from core import views


app_name = 'learning'  # for namespacing


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),

    path('', views.learning, name='learning'),
    
    # Individual lesson URLs (matching your file names: 1.html, 2.html, etc.)
    path('lesson/1/', views.lesson_detail, {'lesson_number': 1}, name='lesson1'),
    path('lesson/2/', views.lesson_detail, {'lesson_number': 2}, name='lesson2'),
    path('lesson/3/', views.lesson_detail, {'lesson_number': 3}, name='lesson3'),
    path('lesson/4/', views.lesson_detail, {'lesson_number': 4}, name='lesson4'),
    path('lesson/5/', views.lesson_detail, {'lesson_number': 5}, name='lesson5'),

    path('forecast/', include('forecast.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
