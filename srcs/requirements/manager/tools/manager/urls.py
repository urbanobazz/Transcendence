from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register),
    path("login/", views.login),
    path("logout/", views.logout),
    path("users/", views.user),
    path("users/avatar/", views.avatar),
    path("users/block/", views.block),
    path("friends/", views.friends),
    path("search/", views.search),
    path("multi/", views.multi),
    path("multi/create/", views.createMulti),
    path("multi/join/", views.joinMulti),
    path("tournaments/", views.tournaments),
    path("tournaments/join/", views.tournaments),
    path("tournaments/create/", views.createTournament),
    path("tournaments/run/", views.tournamentRun),
    path("tournaments/info/", views.tournamentInfo),
    path("tournaments/rank/", views.tournamentRank),
    path("tournaments/leave/", views.tournamentLeave),
    path("chat/", views.chat),
    path("invite/", views.invite),
    path("token/refresh/", views.tokenRefresh),
    path("auth/oauth-callback/", views.oauth_callback),
    path("auth/avatar/", views.upload_avatar),
]
