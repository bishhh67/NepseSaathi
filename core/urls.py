# nepse_sathi/urls.py
from django.urls import path, include
from . import views
from django.contrib import admin 

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path('learn/', views.learning, name='learning'),
    path('admin/', admin.site.urls),
    path('', include('stock_analysis.urls')),  # Simple include, no namespace
    
]