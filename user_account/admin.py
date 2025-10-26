from django.contrib import admin
from .models import UserAccount

# Simple registration - Django will handle everything automatically
admin.site.register(UserAccount)