from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    path('create/<uuid:tournament_id>', views.new_team_form, name='create_team_form'),
    path('<uuid:team_id>/', views.edit_team_form, name='edit_team_form'),
]
