from django.contrib import admin
from .models import TradeOrder,TradesTaken,TradeHistory,ClosedTrades,MarginLocked
# Register your models here.

admin.site.register(TradeOrder)
admin.site.register(TradesTaken)
admin.site.register(ClosedTrades)
admin.site.register(TradeHistory)
admin.site.register(MarginLocked)