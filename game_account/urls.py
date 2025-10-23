from django.urls import path
from .views import (
    game_accounts_list_create,
    GameAccountDetail,
    select_widget,
    list_page,
    form_partial,
    detail_page,
)

app_name = 'game_account'

urlpatterns = [
    # JSON API endpoints (used by AJAX)
    path('game-accounts/', game_accounts_list_create, name='gameaccount-list-create'),
    path('game-accounts/<uuid:pk>/', GameAccountDetail.as_view(), name='gameaccount-detail'),
    path('game-accounts/select_widget/', select_widget, name='gameaccount-select-widget'),

    # HTML pages and fragments
    path('game-accounts/manage/', list_page, name='gameaccount-manage'),
    path('game-accounts/_form/', form_partial, name='gameaccount-form-partial'),
    path('game-accounts/html/<uuid:pk>/', detail_page, name='gameaccount-detail-page'),
]