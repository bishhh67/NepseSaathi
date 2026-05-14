# stock_analysis/admin.py

from django.contrib import admin
from .models import StockDailyData

@admin.register(StockDailyData)
class StockDailyDataAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'date', 'close_price', 'change_percent', 'volume']
    list_filter = ['symbol']
    search_fields = ['symbol']
    date_hierarchy = 'date'
    ordering = ['-date', 'symbol']