from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import UserAccount

class LoginForm(forms.Form):
    """Form for user login"""
    username_or_email = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username atau Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

class RegisterForm(forms.ModelForm):
    """Form for user registration - Step 1"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••'
        })
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••'
        })
    )
    
    class Meta:
        model = UserAccount
        fields = ['username', 'email', 'display_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display Name'
            }),
        }
    
    def clean_username(self):
        """Validate username is unique among active users"""
        username = self.cleaned_data.get('username')
        if UserAccount.objects.filter(username=username, is_active=True).exists():
            raise ValidationError('Username already exists')
        return username
    
    def clean_email(self):
        """Validate email is unique among active users"""
        email = self.cleaned_data.get('email')
        if UserAccount.objects.filter(email=email, is_active=True).exists():
            raise ValidationError('Email already registered')
        return email
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with hashed password"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password'
        })
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })
    )
    
    class Meta:
        model = UserAccount
        fields = ['display_name', 'email', 'profile_image']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'profile_image': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('avatar1', 'Avatar 1'),
                ('avatar2', 'Avatar 2'),
                ('avatar3', 'Avatar 3'),
            ]),
        }
    
    def clean_email(self):
        """Validate email is unique among active users (excluding current user)"""
        email = self.cleaned_data.get('email')
        if UserAccount.objects.filter(email=email, is_active=True).exclude(id=self.instance.id).exists():
            raise ValidationError('Email already registered')
        return email
    
    def clean(self):
        """Validate password change"""
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # If user wants to change password
        if new_password or confirm_password:
            if not current_password:
                raise ValidationError('Current password is required to change password')
            
            if not self.instance.check_password(current_password):
                raise ValidationError('Current password is incorrect')
            
            if new_password != confirm_password:
                raise ValidationError('New passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with optional password change"""
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        
        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()
        return user

class CreateOrganizerForm(forms.ModelForm):
    """Form for admin to create organizer account"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••'
        })
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••••'
        })
    )
    
    class Meta:
        model = UserAccount
        fields = ['username', 'email', 'display_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display Name'
            }),
        }
    
    def clean_username(self):
        """Validate username is unique among active users"""
        username = self.cleaned_data.get('username')
        if UserAccount.objects.filter(username=username, is_active=True).exists():
            raise ValidationError('Username already exists')
        return username
    
    def clean_email(self):
        """Validate email is unique among active users"""
        email = self.cleaned_data.get('email')
        if UserAccount.objects.filter(email=email, is_active=True).exists():
            raise ValidationError('Email already registered')
        return email
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save organizer with hashed password"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'organizer'
        if commit:
            user.save()
        return user