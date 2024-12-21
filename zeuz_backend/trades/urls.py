from django.urls import path
from .views import TradeCreateView,UserTradesView,FuturesCreateView,TradeHistoryView,OptionCreateView,OptionsCreateView,ClosedTradesView,TradeCreateViews
# from .views import TradesTakenView, ClosedTradesView, TradeHistoryView

urlpatterns = [
    path("trades/", UserTradesView.as_view(), name="trades"),
    path('trade/<int:trade_id>/', TradeHistoryView.as_view(), name='trade-history'),
    path('closed-trades/', ClosedTradesView.as_view(), name='closed-trades'),

    # path('create-trades/',TradeCreateView.as_view(), name="create"),
    
    # """this is tempory url for testing LMT and MKT orderes"""
    path('create-trades/',TradeCreateViews.as_view(), name="create"),
    path('create-futures/',FuturesCreateView.as_view(), name="futures"),
    path('create-options/',OptionsCreateView.as_view(), name="options"),
    # path('api/user/trades/', UserTradesView.as_view(), name='user-trades')
#     path("trades/close/", ClosedTradesView.as_view(), name="close_trade"),
#     path("trades/<int:trade_id>/history/", TradeHistoryView.as_view(), name="trade_history"),
]
