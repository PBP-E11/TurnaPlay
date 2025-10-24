from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """
    Admin interface untuk UserAccount.
    """
    # Field yang ditampilkan di list
    list_display = ['username', 'email', 'display_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'display_name']
    
    # Field yang bisa diedit
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('display_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_active')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Field saat add user baru
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'display_name', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    ordering = ['-date_joined']