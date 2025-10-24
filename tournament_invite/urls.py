from django.urls import path
from . import views

app_name = 'tournament_invite'

urlpatterns = [
    # page (list incoming/outgoing)
    path('', views.invite_list, name='invite_list'), # Was 'invites/'

    # actions
    path('create/', views.create_invite, name='create_invite'), # Was 'invites/create/'
    path('<uuid:invite_id>/accept/', views.accept_invite, name='accept_invite'),
    path('<uuid:invite_id>/reject/', views.reject_invite, name='reject_invite'),
    path('<uuid:invite_id>/cancel/', views.cancel_invite, name='cancel_invite'),

    # ajax poll for one-time popup
    path('check/', views.check_new_invite, name='check_new_invite'), # Was 'invites/check/'
]