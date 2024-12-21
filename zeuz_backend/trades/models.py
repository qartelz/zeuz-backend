from django.db import models
from account.models import User

from django.db import models
from account.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    #  choice  for selecting the trades based on the user coice 
    PRODUCT_TYPE_CHOICES = [
        ('Delivery', 'Delivery'),
        ('Intraday', 'Intraday'),
    ]
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
    product_type = models.CharField(
        max_length=30,
        choices=PRODUCT_TYPE_CHOICES,
        null=False,
        blank=False,
        default="Delivery"
    ) #select whether Intraday or Delivery
    segment = models.CharField(max_length=100, default="EQ")
    option_type = models.CharField(max_length=20, blank=True, null=True)
    trade_type = models.CharField(max_length=10, null=False, blank=True)  # Buy or Sell
    avg_price = models.FloatField(null=False, blank=True)  # Average price of holdings
    prctype = models.CharField(max_length=10, null=False, blank=True)  # MKT or LMT
    invested_coin = models.FloatField(null=False, blank=True)  # Total investment value
    margin_required = models.FloatField(
        null=True, blank=True, default=0.0
    )  # Profit/Loss percentage
    trade_status = models.CharField(
        max_length=100, default="incomplete", null=True
    )  # Status
    ticker = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.trading_symbol}"

    def save(self, *args, **kwargs):
        # If quantity becomes 0, change the trade status to 'completed'
        if self.quantity == 0:
            self.trade_status = "completed"
        super().save(*args, **kwargs)


class MarginLocked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    margin = models.FloatField(null=True, blank=True, default=0.0)

    def __str__(self):
        return f"{self.user} - {self.margin}"

    # Signal to create MarginLocked instance


@receiver(post_save, sender=User)
def create_margin_locked(sender, instance, created, **kwargs):
    if created:  # Only create when a new User is created
        MarginLocked.objects.create(user=instance)


class ClosedTrades(models.Model):
    trade = models.ForeignKey(
        TradesTaken, on_delete=models.CASCADE, related_name="closed_trades"
    )
    sell_quantity = models.IntegerField(null=False)  # Quantity sold
    product_type = models.CharField(max_length=100,null=False)
    avg_price = models.FloatField(null=False,default=0)  # avg buy price when sold
    sell_price = models.FloatField(null=False)  # Selling price per unit
    sell_date = models.DateTimeField(auto_now_add=True)  # Date of the sell transaction
    profit_loss = models.DecimalField(
        max_digits=10, decimal_places=2, null=False
    )  # Profit or loss from the sell transaction

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
    trade = models.ForeignKey(
        TradesTaken, on_delete=models.CASCADE, related_name="trade_history"
    )
    trade_type = models.CharField(max_length=10, null=False, blank=True)  # Buy or Sell
    quantity = models.IntegerField(null=False, blank=True)
    trade_price = models.FloatField(
        null=False, blank=True
    )  # Price at which trade occurred
    timestamp = models.DateTimeField(auto_now_add=True)
    # created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trade.trading_symbol} - {self.trade_type} - {self.quantity}"



"""this model is for saving LMT orders when placed by the user for placing trades"""

class LimitOrder(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('Delivery', 'Delivery'),
        ('Intraday', 'Intraday'),
    ]

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
    product_type = models.CharField(
        max_length=30,
        choices=PRODUCT_TYPE_CHOICES,
        null=False,
        blank=False,
        default="Delivery"
    ) #select whether Intraday or Delivery
    segment = models.CharField(max_length=100, default="EQ")
    option_type = models.CharField(max_length=20, blank=True, null=True)
    trade_type = models.CharField(max_length=10, null=False, blank=True)  # Buy or Sell
    avg_price = models.FloatField(null=False, blank=True)  # Average price of holdings
    prctype = models.CharField(max_length=10, null=False, blank=True)  # MKT or LMT
    invested_coin = models.FloatField(null=False, blank=True)  # Total investment value
    executed = models.BooleanField(default=False)  # Executed status instead of margin_required
    trade_status = models.CharField(
        max_length=100, default="incomplete", null=True
    )  # Status
    ticker = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def _str_(self):
        return f"{self.user} - {self.trading_symbol}"
    
    # def create(self, validated_data):
    #     # Handle custom logic here if necessary
    #     return super().create(validated_data)

    def to_dict(self):
        return {
            "user": self.user,
            "token_id": self.token_id,
            "exchange": self.exchange,
            "trading_symbol": self.trading_symbol,
            "series": self.series,
            "lot_size": self.lot_size,
            "quantity": self.quantity,
            "display_name": self.display_name,
            "company_name": self.company_name,
            "expiry_date": self.expiry_date,
            "segment": self.segment,
            "option_type": self.option_type,
            "trade_type": self.trade_type,
            "avg_price": self.avg_price,
            "prctype": self.prctype,
            "invested_coin": self.invested_coin,
            "trade_status": self.trade_status,
            "ticker": self.ticker,
            "product_type": self.product_type,
        }
