# nepse_sathi/urls.py
from django.urls import path, include
from . import views
from django.contrib import admin 

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path('learn/', views.learning, name='learning'),
    path('admin/', admin.site.urls),
    path('', include('stock_analysis.urls')),
      
        # Simple include, no namespace
    path('learn/', views.learning, name='learning'),
    
    # Individual lesson URLs
    path('learn/lesson/1/', views.lesson_detail, {'lesson_number': 1}, name='lesson1'),
    path('learn/lesson/2/', views.lesson_detail, {'lesson_number': 2}, name='lesson2'),
    path('learn/lesson/3/', views.lesson_detail, {'lesson_number': 3}, name='lesson3'),
    path('learn/lesson/4/', views.lesson_detail, {'lesson_number': 4}, name='lesson4'),
    path('learn/lesson/5/', views.lesson_detail, {'lesson_number': 5}, name='lesson5'),



    path('livemarket/', views.live_market, name='live_market'),
    path('api/market-data/', views.get_market_data, name='get_market_data'),
    path('api/scrape/', views.trigger_scraper, name='trigger_scraper'),
]
