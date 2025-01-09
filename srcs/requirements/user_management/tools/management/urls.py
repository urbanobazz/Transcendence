from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views_game, views_token, views_tournament, views_user
from rest_framework_simplejwt.views import (
	TokenObtainPairView,
	TokenRefreshView,
)

urlpatterns = [
	# path("login/", views.login),
	path("register/", views_user.register),
	path("user/", views_user.userManagement),
	path("user/validate/", views_user.findUser),
	path("user/avatar/", views_user.avatarUpload),
	path("friends/", views_user.listFriends),
	path("friends/manage/", views_user.manageFriends),
	path("friends/blocked/", views_user.manageBlocked),
	path("friends/listblocked/", views_user.listBlockedUsers),
	path("search/", views_user.listUsers),
	path("multi/", views_game.listGames),
	path("multi/join/", views_game.joinMulti),
	path("multi/create/", views_game.createMulti),
	path("multi/validate/", views_game.validateMulti),
	path("multi/archive/", views_game.archiveGame),
	path("multi/delete/", views_game.deleteGame),
	path("tournaments/", views_tournament.listTournaments),
	path("tournaments/join/", views_tournament.joinTournament),
	path("tournaments/create/", views_tournament.createTournament),
	path("tournaments/run/", views_tournament.runTournament),
	path("tournaments/rank/", views_tournament.getTournamentRanking),
	path("tournaments/players/", views_tournament.getTournamentPlayers),
	path("tournaments/info/", views_tournament.getTournamentInfo),
	path("tournaments/leave/", views_tournament.leaveTournament),
	path("tournaments/getname/", views_tournament.getName),
	path('token/', views_token.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('token/refresh/', views_token.CustomTokenRefreshView.as_view(), name='token_refresh'),
	path("validate-token/", views_user.validate_token),
	path("ping/", views_user.ping),
	path("chat/game/", views_game.createChatGame)
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
