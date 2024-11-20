from django.db import models

class UploadedFile(models.Model):
    file_name = models.CharField(max_length=255)
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class TradingInstrument(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name="instruments")
    token_id = models.CharField(max_length=100)
    exchange = models.CharField(max_length=100)
    trading_symbol = models.CharField(max_length=100)
    series = models.CharField(max_length=10, blank=True, null=True)
    script_name = models.CharField(max_length=255, blank=True, null=True)
    ticker = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.CharField(blank=True, null=True)
    option_type = models.CharField(max_length=20, blank=True, null=True)
    segment = models.CharField(max_length=50)
    lot_size = models.IntegerField()
    tick_size = models.FloatField()
    strike_price = models.FloatField(blank=True, null=True)
    display_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    instrument_name = models.CharField(max_length=255, blank=True, null=True)
    isin_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.trading_symbol} ({self.exchange})"
    
    class Meta:
        indexes = [
            models.Index(fields=['exchange']),
            models.Index(fields=['segment']),
            models.Index(fields=['script_name']),
            models.Index(fields=['exchange', 'segment']),  # Combined index
        ]


