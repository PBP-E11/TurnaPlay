from django.urls import path, include
from tournaments.views import show_main, tournament_create
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('', show_main, name='show_main'),
    # Temporary safe mapping: render main page until TournamentListView is implemented
    path('tournaments/', show_main, name='tournament-list'),
    
    # --- Create tournament (function view) ---
    path('tournaments/create/', tournament_create, name='tournament-create'),
    path('tournaments/<uuid:pk>/', views.tournament_detail, name='tournament-detail'),
    
    path('api/tournaments/', views.tournament_list_json, name='tournament-list-json'),
    path('api/games/<uuid:game_id>/formats/', views.formats_for_game, name='api-game-formats'),

    path('<uuid:pk>/update/', views.tournament_update, name='tournament-update'),
    path('<uuid:pk>/delete/', views.tournament_delete, name='tournament-delete'),
]