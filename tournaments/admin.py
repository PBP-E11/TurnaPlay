from django.contrib import admin
from .models import Game, TournamentFormat, Tournament

# Register your models to make them visible in the admin area
admin.site.register(Game)
admin.site.register(TournamentFormat)
admin.site.register(Tournament)
