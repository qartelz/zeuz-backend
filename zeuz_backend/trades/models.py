from django.db import models
from account.models import User
# from account.models import BeetleCoins

class TradeOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    trading_symbol = models.CharField(max_length=10)  
    display_name = models.CharField(max_length=255)  
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order_type = models.CharField(max_length=20) 
    transaction_type = models.CharField(max_length=20) 
    status = models.CharField(max_length=20, default="Pending") 
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.display_name} - {self.trading_symbol} ({self.transaction_type})"

    class Meta:
        verbose_name = "Trade Order"
        verbose_name_plural = "Trade Orders"

    class Meta:
        verbose_name = "Trade Order"
        verbose_name_plural = "Trade Orders"



class TradesTaken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_id = models.CharField(max_length=50, null=False, blank=True)
    exchange = models.CharField(max_length=50, null=False, blank=True)
    trading_symbol = models.CharField(max_length=50, null=False, blank=True)
    series = models.CharField(max_length=10, null=False, blank=True)  # EQ
    lot_size = models.IntegerField(null=False, blank=True)  # Default value from DB
    quantity = models.IntegerField(null=False, blank=True)  # Total quantity held
    display_name = models.CharField(max_length=100, null=False, blank=True)
    company_name = models.CharField(max_length=100, null=False, blank=True)
    expiry_date = models.CharField(blank=True, null=True)
    segment = models.CharField(max_length=100, default="EQ")
    option_type = models.CharField(max_length=20, blank=True, null=True)
    trade_type = models.CharField(max_length=10, null=False, blank=True)  # Buy or Sell
    avg_price = models.FloatField(null=False, blank=True)  # Average price of holdings
    prctype = models.CharField(max_length=10, null=False, blank=True)  # MKT or LMT
    invested_coin = models.FloatField(null=False, blank=True)  # Total investment value
    profit_loss = models.FloatField(null=True, blank=True,default=0.0)  # Profit/Loss percentage
    trade_status = models.CharField(max_length=100, default="incomplete", null=True) # Status
    ticker = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.user} - {self.trading_symbol}"
    
    def save(self, *args, **kwargs):
        # If quantity becomes 0, change the trade status to 'completed'
        if self.quantity == 0:
            self.trade_status = "completed"
        super().save(*args, **kwargs)


class ClosedTrades(models.Model):
    trade = models.ForeignKey(TradesTaken, on_delete=models.CASCADE, related_name="closed_trades")
    sell_quantity = models.IntegerField(null=False)  # Quantity sold
    sell_price = models.FloatField(null=False)  # Selling price per unit
    sell_date = models.DateTimeField(auto_now_add=True)  # Date of the sell transaction
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2,null=False)  # Profit or loss from the sell transaction

    def __str__(self):
        return f"Closed {self.sell_quantity} of {self.trade.trading_symbol}"
        # return {self.trade}

    # def save(self, *args, **kwargs):
    #     """
    #     Automatically calculate profit/loss when a closed trade is saved.
    #     """
    #     buy_price = self.trade.avg_price
    #     self.profit_loss = (self.sell_price - buy_price) * self.sell_quantity
    #     super().save(*args, **kwargs)


class TradeHistory(models.Model):
    trade = models.ForeignKey(TradesTaken, on_delete=models.CASCADE, related_name="trade_history")
    trade_type = models.CharField(max_length=10, null=False, blank=True)  # Buy or Sell
    quantity = models.IntegerField(null=False, blank=True)
    trade_price = models.FloatField(null=False, blank=True)  # Price at which trade occurred
    timestamp = models.DateTimeField(auto_now_add=True)
    # created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trade.trading_symbol} - {self.trade_type} - {self.quantity}"
