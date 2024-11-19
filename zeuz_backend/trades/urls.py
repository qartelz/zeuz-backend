from django.urls import path
from .views import TradeCreateView,UserTradesView
# from .views import TradesTakenView, ClosedTradesView, TradeHistoryView

urlpatterns = [
    path("trades/", UserTradesView.as_view(), name="trades"),
    path('create-trades/',TradeCreateView.as_view(), name="create"),
    # path('api/user/trades/', UserTradesView.as_view(), name='user-trades')
#     path("trades/close/", ClosedTradesView.as_view(), name="close_trade"),
#     path("trades/<int:trade_id>/history/", TradeHistoryView.as_view(), name="trade_history"),
]
