from django.urls import path
from . import views

app_name = 'tournament_invite'

urlpatterns = [
    # page (list incoming/outgoing)
    path('invites/', views.invite_list, name='invite_list'),

    # actions
    path('invites/create/', views.create_invite, name='create_invite'),
    path('invites/<uuid:invite_id>/accept/', views.accept_invite, name='accept_invite'),
    path('invites/<uuid:invite_id>/reject/', views.reject_invite, name='reject_invite'),
    path('invites/<uuid:invite_id>/cancel/', views.cancel_invite, name='cancel_invite'),

    # ajax poll for one-time popup
    path('invites/check/', views.check_new_invite, name='check_new_invite'),
]