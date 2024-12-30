from django.urls import path
from .views import CSVUploadView,TradingInstrumentSearchView,GroupedOptionsView,SearchView

urlpatterns = [
   
     path('upload-csv/', CSVUploadView.as_view(), name='upload-csv'),
     path('search/', TradingInstrumentSearchView.as_view(), name='trading_instrument_search'),
     path('optionchain/',GroupedOptionsView.as_view(), name='option_chain'),
     path('searchs/', SearchView.as_view(), name='trading_instrument_search'),
     # path('search-options/', InstrumentSearchOptions.as_view(), name='instrument-search-options'),
     # path('option-chain/',OptionChainViews.as_view(), name='option_chain')
]