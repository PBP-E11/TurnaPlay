from django.urls import path
from . import views

app_name = "tournament_invite"

urlpatterns = [
    # pages
    path("invites/", views.invite_list, name="invite-list"),

    # create (leader only)
    path("invites/create/", views.create_invite, name="create-invite"),

    # JSON polling (toast)
    path("invites/check/", views.check_new_invite, name="check-new-invite"),

    # JSON actions (AJAX)
    path("api/accept/", views.api_accept_invite, name="api-accept"),
    path("api/reject/", views.api_reject_invite, name="api-reject"),
    path("api/cancel/", views.api_cancel_invite, name="api-cancel"),
]