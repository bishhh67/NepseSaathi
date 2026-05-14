# stock_analysis/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('why-moved/', views.stock_search, name='stock_search'),
    path('why-moved/<str:symbol>/<int:year>/<int:month>/<int:day>/', 
         views.analysis_result, 
         name='analysis_result'),
    path('analyze/', views.analysis_result_by_form, name='analysis_result_by_form'),
    path('api/autocomplete/', views.autocomplete_symbols, name='autocomplete'),
    path('api/dates/<str:symbol>/', views.get_available_dates, name='available_dates'),
]