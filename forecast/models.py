# forecast/models.py
from django.db import models

class Company(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        db_table = 'companies'
        managed = False  # Don't let Django manage this table (SQLite already exists)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"

class StockHistory(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    date = models.DateField()
    change = models.FloatField(blank=True, null=True)
    change_pct = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    turnover = models.FloatField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    trade = models.IntegerField(blank=True, null=True)
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    
    class Meta:
        db_table = 'stock_history'
        managed = False
        ordering = ['-date']