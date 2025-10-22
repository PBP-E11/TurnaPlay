from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameAccountViewSet

router = DefaultRouter() # Used a router so the endpoints are automatic
router.register(r'game-accounts', GameAccountViewSet, basename='gameaccount')

app_name = 'game_account'

urlpatterns = [
    path('', include(router.urls)),
]