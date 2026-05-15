from django.urls import path
from . import views

app_name = 'forecast'

urlpatterns = [
    path('', views.index, name='index'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('api/generate_graphs/<str:symbol>/', views.generate_graphs_api, name='generate_graphs_api'),
]