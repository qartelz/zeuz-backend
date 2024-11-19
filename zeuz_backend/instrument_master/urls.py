from django.urls import path
from .views import CSVUploadView,TradingInstrumentSearchView

urlpatterns = [
   
     path('upload-csv/', CSVUploadView.as_view(), name='upload-csv'),
     path('search/', TradingInstrumentSearchView.as_view(), name='trading_instrument_search'),
]