from celery import shared_task
from .models import TradesTaken  # Replace with your actual model name
from datetime import datetime

@shared_task
def execute_intraday_trades():
    # Filter trades with 'Intraday' product_type and 'incomplete' trade_status
    trades = TradesTaken.objects.filter(product_type="Intraday", trade_status="incomplete")
    for trade in trades:
        # Add the logic to execute the trade
        print("executed")
        # trade.trade_status = "executed"
        # trade.execution_time = datetime.now()
        # trade.save()
