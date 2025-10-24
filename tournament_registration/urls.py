from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    path('create/<uuid:tournament_id>', views.new_team_form, name='create_team_form'),
    path('<uuid:team_id>/', views.edit_team_form, name='edit_team_form'),
    path('api/<uuid:team_id>/leave_team', views.leave_team, name='leave_team'),
    path('api/<uuid:team_id>/kick_member', views.kick_member, name='kick_member'),
    path('api/<uuid:team_id>/list_members', views.list_members, name='list_members'),
]
