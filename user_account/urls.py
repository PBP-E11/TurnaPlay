from django.urls import path
from . import views

app_name = 'user_account'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('register/complete/', views.complete_profile_view, name='complete_profile'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
    
    # Admin Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_manage_users, name='admin_manage_users'),
    path('users/create-organizer/', views.admin_create_organizer, name='admin_create_organizer'),
    path('users/<uuid:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<uuid:user_id>/deactivate/', views.admin_deactivate_user, name='admin_deactivate_user'),
]