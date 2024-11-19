
from django.contrib import admin
from .models import User, Profile, BeetleCoins

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'phone_number', 'is_active', 'is_staff', 'is_admin', 'date_joined')
    search_fields = ('email', 'name', 'phone_number')
    list_filter = ('is_active', 'is_staff', 'is_admin')
    ordering = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ()}),  
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone_number', 'password1', 'password2')}
        ),
    )



admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'address', 'city', 'last_updated')
    search_fields = ('user__email', 'user__name')
    list_filter = ('last_updated',)
    ordering = ('user__email',)

@admin.register(BeetleCoins)
class BeetleCoinsAdmin(admin.ModelAdmin):
    list_display = ('user', 'coins', 'used_coins')
    search_fields = ('user__email', 'user__name')
    list_filter = ('coins', 'used_coins')
    ordering = ('user__email',)
