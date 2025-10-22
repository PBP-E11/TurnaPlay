import uuid
from django.http import HttpRequest
from django.shortcuts import render
from .models import TournamentRegistration

def create_team(request: HttpRequest):
    return render(request, 'team/forms.html')

def manage_team(request: HttpRequest, id: uuid):
    pass
