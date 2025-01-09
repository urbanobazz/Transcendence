from .models import UserStats, User, Game, Tournament
import logging, json


# Functions to create objects
def create_game(users=None, round=0, tournament=None, **kwargs):
	game = Game.objects.create(can_join=True, round=round, tournament=tournament, **kwargs)
	if users:
		if isinstance(users, list):
			for i, user in enumerate(users):
				if i == 0:
					game.player1 = user
				elif i == 1:
					game.player2 = user
				else:
					break
		else:
			game.player1 = users
		game.save()
		if game.tournament:
			tournament = Tournament.objects.get(id=game.tournament.id)
			tournament.matches.add(game)
	return game

def create_tournament(name=None, owner=None, num_players=0, **kwargs):
	tournament = Tournament.objects.create(name=name, owner=owner, n_players=num_players, **kwargs)
	return tournament

def getUserFromId(request):
	data = json.loads(request.body)
	user_id = data.get('user_id')

	try:
		user = User.objects.get(id=user_id)
		return user

	except Exception as e:
		return None

def getUserData(profile, user=None):
	return {
		'id': profile.id,
		'username': profile.username,
		'create_date': profile.create_date,
		'friends': [friend.id for friend in profile.friends.all()],
		'blocked': [blocked.id for blocked in profile.blocked.all()],
		'stats': getStatsData(profile.stats),
		'avatar': profile.avatar.url if profile.avatar else None,
		'is_friend': profile in user.friends.all() if user else False,
		'is_blocked': profile in user.blocked.all() if user else False
	}

def getStatsData(stats):
	return {
		'user': stats.user.id,
		'games_played': [getGameData(game) for game in stats.games_played.all() if game.winner],
		'wins': stats.wins,
		'losses': stats.losses,
		'avg_duration': stats.avg_duration
	}

def getGameData(game):
	return {
		'id': game.id,
		'duration': game.duration,
		'winner': game.winner.username if game.winner else '',
		'p1': game.player1.username if game.player1 else '',
		'p2': game.player2.username if game.player2 else '',
		'p1_score': game.scores.get('score1', 0),
		'p2_score': game.scores.get('score2', 0),
		'can_join': game.can_join,
		'closed': game.closed
	}
#Expected output:
# {
#     "id": "G-1234",
#     "duration": "1:30:00",
#     "winner": "U-5678",
#     "player1": "U-1234",
#     "player2": "U-4321",
#     "scores": {
#         "score1": 100,
#         "score2": 150
#     },
#     "can_join": false,
#     "closed": true
# }
