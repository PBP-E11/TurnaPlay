from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    path('create/', views.create_team, name='create_team'),
    path('<uuid:id>/', views.manage_team, name='manage_team'),
]
