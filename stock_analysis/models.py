from django.db import models


class StockDailyData(models.Model):
    symbol       = models.CharField(max_length=20, db_index=True)
    date         = models.DateField(db_index=True)
    change       = models.FloatField(default=0.0)
    change_percent = models.FloatField(default=0.0)
    close_price  = models.FloatField()
    turnover     = models.FloatField(default=0.0)
    volume       = models.BigIntegerField(default=0)
    trade_count  = models.IntegerField(default=0)
    open_price   = models.FloatField(default=0.0)
    high_price   = models.FloatField(default=0.0)
    low_price    = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("symbol", "date")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["symbol", "date"]),
        ]

    def __str__(self):
        return f"{self.symbol} | {self.date} | Close: {self.close_price}"