from django.contrib import admin
from .models import TeamMember, TournamentRegistration

# Register your models here.
admin.site.register(TeamMember)
admin.site.register(TournamentRegistration)
