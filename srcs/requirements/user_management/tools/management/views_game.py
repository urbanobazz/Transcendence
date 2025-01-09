from .models import Game, User
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .utils import create_game, getUserFromId
from .views_user import is_blocked
import logging, json


logger = logging.getLogger('management')

@csrf_exempt
def createMulti(request):
	if request.method == 'POST':
		user = getUserFromId(request)
		data = json.loads(request.body)
		game_name = data.get('game_name')
		game_speed = data.get('game_speed')
		power_ups = data.get('power_ups')

		if not user:
			return JsonResponse({'message': 'Invalid user id.'}, status=401)

		game = create_game(user, name=game_name, speed=game_speed, power_ups=power_ups)
		user.stats.games_played.add(game)
		return JsonResponse({'message': 'Multiplayer game created successfully!', 'id' : game.id}, status=201)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def joinMulti(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		game_id = data.get('game_id')
		user = getUserFromId(request)
		if not user:
			return JsonResponse({'message': 'Invalid token.'}, status=401)
		elif not game_id:
			return JsonResponse({'message': 'Game ID is required.'}, status=400)

		try:
			game = Game.objects.get(id=game_id)
		except Game.DoesNotExist:
			return JsonResponse({'message': 'Game not found.'}, status=404)

		if not game.can_join:
			return JsonResponse({'message': 'Game is closed.'}, status=400)

		if game.player1 == user or game.player2 == user:
			return JsonResponse({'message': 'User already in game.'}, status=200)
		game.player2 = user
		user.stats.games_played.add(game)
		game.can_join = False
		game.start_date = timezone.now()
		game.save()
		return JsonResponse({'message': 'User joined game successfully!'}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def listGames(request):
	if request.method == 'POST':
		games = Game.objects.all()
		user = getUserFromId(request)
		if not games:
			return JsonResponse({}, status=200, safe=False)
		if not user:
			return JsonResponse({'message': 'userID required'}, status=401)

		game_list = []
		for game in games:
			if game.can_join:
				if not is_blocked(user, game.player1) and not game.tournament:
					game_list.append({
						'id': game.id,
						'name': game.name,
					})
		return JsonResponse(game_list, status=200, safe=False)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def validateMulti(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		game_id = data.get('game_id')
		if not game_id:
			return JsonResponse({'message': 'Game ID is required.'}, status=400)

		try:
			game = Game.objects.get(id=game_id)
		except Game.DoesNotExist:
			return JsonResponse({'message': 'Game not found.'}, status=404)

		response = {
			'id': game.id if not game.closed else '',
			'p1': game.player1.id if game.player1 else '',
			'p2': game.player2.id if game.player2 else '',
			'speed': game.speed,
			'power_ups': game.power_ups
		}
		return JsonResponse(response, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def archiveGame(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		game_id = data.get('game_id')
		scores = data.get('scores')
		p1 = data.get('p1')
		p2 = data.get('p2')
		game_speed = data.get('game_speed')
		power_ups = data.get('power_ups')

		if not game_id:
			return JsonResponse({'message': 'Game ID is required.'}, status=400)

		try:
			if game_id.startswith('GAI-'):
				game = handle_ai(p1, p2, game_speed, power_ups)
			else:
				game = Game.objects.get(id=game_id)
		except Game.DoesNotExist:
			return JsonResponse({'message': 'Game not found.'}, status=404)
		if game.closed:
			return JsonResponse({'message': 'Game already closed.'}, status=200)
		# Proccess scores and wiinner
		if scores:
			if game.player1.id == p1:
				score1 = int(scores.get('score1', 0))
				score2 = int(scores.get('score2', 0))
			else: # Flip the scores if players are not in the right order
				score2 = int(scores.get('score1', 0))
				score1 = int(scores.get('score2', 0))
				scores = {'score1': score1, 'score2': score2}

			if score1 > score2:
				game.winner = game.player1
				game.player1.stats.wins += 1
				game.player2.stats.losses += 1
			else:
				game.winner = game.player2
				game.player2.stats.wins += 1
				game.player1.stats.losses += 1

		if game.tournament:
			game.player1.stats.games_played.add(game)
			game.player2.stats.games_played.add(game)
			game.player1.stats.save()
			game.player2.stats.save()

		game.closed = True
		game.can_join = False
		game.end_date =  timezone.now()
		game.duration = game.end_date - game.start_date
		game.scores = scores
		game.save()
		game.player1.stats.save()
		game.player2.stats.save()
		logger.info(f'Game archived: {game.winner.username} wins')
		return JsonResponse({'message': 'Game archived successfully.'}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

# ## EXAMPLE of the expected request
# {
#     "game_id": 1,
#     "scores": {
#         "score1": 100,
#         "score2": 150
#     },
#     "winner": 2,
#     "p1": 1,
#     "p2": 2
# }

def handle_ai(p1, p2, speed, power_ups):
	p1 = User.objects.get(id=p1)
	p2 = User.objects.get(id=p2)
	game = create_game(users=[p1, p2], speed=speed, power_ups=power_ups)
	game.start_date = timezone.now()
	p1.stats.games_played.add(game)
	p2.stats.games_played.add(game)
	game.save()
	return game

@csrf_exempt
def createChatGame(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		game_id = data.get('game_id')
		user = getUserFromId(request)
		user2 = data.get('friend')

		try:
			friend = User.objects.get(id=user2)
		except Exception as e:
			friend =  None

		if not user or not friend:
			return JsonResponse({'message': 'Player not found'}, status=401)

		game = create_game([user, friend]) #Should we incluede power_ups and speed?
		user.stats.games_played.add(game)
		friend.stats.games_played.add(game)
		game.can_join = False
		game.save()
		return JsonResponse({'message': 'Chat game created successfully!', 'id' : game.id}, status=201)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def deleteGame(request):
	if request.method == 'DELETE':
		data = json.loads(request.body)
		game_id = data.get('game_id')
		user = getUserFromId(request)

		if not user:
			return JsonResponse({'message': 'Invalid token.'}, status=401)

		try:
			game = Game.objects.get(id=game_id)
		except Game.DoesNotExist:
			return JsonResponse({'message': 'Game not found.'}, status=404)

		if game.player1 == user or game.player2 == user:
			game.delete()
			return JsonResponse({'message': 'Game deleted successfully!'}, status=200)
		else:
			return JsonResponse({'message': 'User not authorized to delete game.'}, status=401)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)
