from django.contrib import admin
from .models import TradingInstrument, UploadedFile

class TradingInstrumentInline(admin.TabularInline):
    model = TradingInstrument
    fields = (
        'token_id', 'exchange', 'trading_symbol', 'series', 'script_name', 
        'ticker', 'expiry_date', 'option_type', 'segment', 'lot_size', 
        'tick_size', 'strike_price', 'display_name', 'company_name', 
        'instrument_name', 'isin_number'
    )
    extra = 0  


class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'upload_time')  
    search_fields = ('file_name',)  
    inlines = [TradingInstrumentInline]  


class TradingInstrumentAdmin(admin.ModelAdmin):
    list_display = (
        'token_id', 'exchange', 'trading_symbol', 'series', 'script_name', 
        'ticker', 'expiry_date', 'option_type', 'segment', 'lot_size', 
        'tick_size', 'strike_price', 'display_name', 'company_name', 
        'instrument_name', 'isin_number'
    )
    list_filter = ('exchange', 'option_type', 'segment','expiry_date')  
    search_fields = ('token_id', 'trading_symbol', 'company_name', 'instrument_name')  
    ordering = ('token_id',)  


admin.site.register(UploadedFile, UploadedFileAdmin)
admin.site.register(TradingInstrument, TradingInstrumentAdmin)
