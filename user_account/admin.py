from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserAccount


class UserAccountCreationForm(UserCreationForm):
    """Custom form for creating new users in Django Admin"""
    
    email = forms.EmailField(required=True, label='Email')
    display_name = forms.CharField(required=False, label='Display Name', 
                                   help_text='Leave blank to use username')
    role = forms.ChoiceField(choices=UserAccount.ROLE_CHOICES, initial='user')
    
    class Meta:
        model = UserAccount
        fields = ('username', 'email', 'display_name', 'role')
    
    def clean_display_name(self):
        """Set display_name to username if empty"""
        display_name = self.cleaned_data.get('display_name')
        if not display_name:
            display_name = self.cleaned_data.get('username')
        return display_name
    
    def save(self, commit=True):
        """Override save to ensure display_name is set"""
        user = super().save(commit=False)
        
        # Ensure display_name is set
        if not user.display_name:
            user.display_name = user.username
        
        # Ensure profile_image is set
        if not user.profile_image:
            user.profile_image = 'avatar1'
        
        if commit:
            user.save()
        return user


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """
    Admin interface untuk UserAccount.
    """
    # Use custom creation form
    add_form = UserAccountCreationForm
    
    # Field yang ditampilkan di list
    list_display = ['username', 'email', 'display_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'display_name']
    
    # Field yang bisa diedit (untuk existing user)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('display_name', 'email', 'profile_image')}),
        ('Permissions', {'fields': ('role', 'is_active')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Field saat add user baru
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'display_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    ordering = ['-date_joined']