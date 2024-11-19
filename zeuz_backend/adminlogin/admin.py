from django.contrib import admin
from .models import Tokens

@admin.register(Tokens)
class TokensAdmin(admin.ModelAdmin):
    # list_display = ('id', 'broadcast_token', 'broadcast_userid')  
    list_display = ('id', 'broadcast_userid')
    search_fields = ('broadcast_token', 'broadcast_userid')  
    list_filter = ('broadcast_userid',)