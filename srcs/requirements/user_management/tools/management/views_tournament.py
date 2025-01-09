from .models import Tournament, Game, TournamentPlayer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import create_tournament, getUserFromId, create_game
from django.utils import timezone
import logging, json, random

# Create your views here.

logger = logging.getLogger('management')

@csrf_exempt
def listTournaments(request):
	if request.method == 'POST':
		user = getUserFromId(request)
		tournaments = Tournament.objects.filter(end_date=None)
		tournament_list = []
		active_tournament = isPlayerBusy(user)
		if not active_tournament:
			for tournament in tournaments:
				if tournament.rounds == 0 and tournament.ready < tournament.n_players:
					tournament_list.append({
						'id': tournament.id,
						'name': tournament.name,
						'start_date': tournament.start_date,
						'duration': tournament.duration,
						'winner': tournament.winner.id if tournament.winner else None,
						'owner': tournament.owner.id
					})
			return JsonResponse(tournament_list, status=200, safe=False)
		else:
			tournament_list.append({
						'id': active_tournament.id,
						'name': active_tournament.name,
						'start_date': active_tournament.start_date,
						'duration': active_tournament.duration,
						'winner': active_tournament.winner.id if active_tournament.winner else None,
						'owner': active_tournament.owner.id
					})
			return JsonResponse(tournament_list, status=200, safe=False)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def createTournament(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_name = data.get('tournament_name')
		n_players = data.get('n_players')
		game_speed = data.get('game_speed')
		power_ups = data.get('power_ups')
		user = getUserFromId(request)
		if not user:
			return JsonResponse({'message': 'Invalid token.'}, status=401)
		elif not tournament_name:
			return JsonResponse({'message': 'Tournament name is required.'}, status=400)
		elif isPlayerBusy(user) != None:
			return JsonResponse({'message': 'Cannot create a new tournament (ALREADY ENROLLED)'}, status=409)

		tournament = create_tournament(tournament_name, user, n_players, speed=game_speed, power_ups=power_ups)
		tournament.addPlayer(user)
		return JsonResponse({'message': 'Tournament created successfully!', 'id': tournament.id}, status=201)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def joinTournament(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('game_id') # game id because fronts end needs it
		user = getUserFromId(request)
		if not user:
			return JsonResponse({'message': 'Invalid token.'}, status=401)
		elif not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		# if tournament.ready == tournament.n_players:
		# 	return JsonResponse({'message': 'Tournament is full.'}, status=400)

		if TournamentPlayer.objects.filter(tournament=tournament, player=user).exists():
			return JsonResponse({'message': 'User already joined tournament.'}, status=200)
		else:
			tournament.addPlayer(user)
			return JsonResponse({'message': 'User joined tournament successfully!'}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def leaveTournament(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('tournament_id')
		user = getUserFromId(request)
		if not user:
			return JsonResponse({'message': 'Invalid token.'}, status=401)
		elif not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		if not TournamentPlayer.objects.filter(tournament=tournament, player=user).exists():
			return JsonResponse({'message': 'User is not in the tournament.'}, status=200)
		else:
			tournament.removePlayer(user)
			return JsonResponse({'message': 'User left tournament successfully!'}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)



@csrf_exempt
def  runTournament(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('tournament_id')
		if not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		logger.info(f"\33[33mReady: {tournament.ready}, N_players: {tournament.n_players}, Rounds: {tournament.rounds}\33")
		if tournament.rounds < 1 and tournament.ready < tournament.n_players:
			return JsonResponse({'message': 'Not enough players to start tournament.'}, status=400)
		elif tournament.rounds >= 1 and tournament.ready + 1 < tournament.n_players:
			tournament.ready += 1
			tournament.save()
			return JsonResponse({'message': 'Not all players are ready to start next round.'}, status=400)
		elif tournament.rounds > 0 and tournament.winner:
			return JsonResponse({'message': 'Tournament is already over.'}, status=400)
		else:
			tournament.ready = 0
			tournament.save()
			return makeRound(tournament)

	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)


def makeRound(tournament):
		tournament.rounds += 1
		tournament.save()
		current_round = tournament.rounds
		#Handle first round
		if current_round <= 1:
			players = list(tournament.players.all())
			if len(players) < 2:
				return JsonResponse({'message': 'Not enough players to create matches.'}, status=400)
		#Handle subsequent rounds
		elif current_round > 1:
			players = getWinners(tournament, current_round - 1)
			logger.info(f"Players: {players}, Current Round: {current_round}")
			#Handle end of tournament
			if len(players) < 2:
				TournamentArchive(tournament, players[0])
				return JsonResponse({'message': 'Tournament is over', 'winner': players[0].username, 'name': tournament.name}, status=200)
			#Handle final round
			elif len(players) == 2:
				game = create_game(users=players, round=current_round, tournament=tournament, speed=tournament.speed, power_ups=tournament.power_ups)
				tournament.n_players /= 2
				tournament.save()
				return JsonResponse({'message': 'Final match created successfully!',
									 'owner': tournament.owner.id,
									 'matches': [{'id': game.id,
												 'p1' : { 'id': game.player1.id,
												 'name': game.player1.username },
												 'p2': {'id' : game.player2.id,
												 'name': game.player2.username,
												 'speed': game.speed,
												 'power_ups': game.power_ups}}]
									}, status=201)

		#Handle all other rounds
		matches = createMatches(tournament, players, current_round)
		tournament.start_date = timezone.now()
		tournament.n_players /= 2
		tournament.save()
		return JsonResponse({'message': 'Matches created successfully!',
							 'owner': tournament.owner.id,
							 'matches': [{'id': match.id,
										 'p1': {'id' : match.player1.id,
										 'name': match.player1.username },
										 'p2': {'id' : match.player2.id if match.player2.id else None,
										 'name': match.player2.username if match.player2 else None },
										 'speed': match.speed,
										 'power_ups': match.power_ups
										} for match in matches]
							}, status=201)

def getWinners(tournament, round):
	matches = Game.objects.filter(tournament=tournament, round=round)
	winners = []
	for match in matches:
		if match.winner:
			winners.append(match.winner)
	return winners

def createMatches(tournament, players, round_number):
	matches = []
	random.shuffle(players)
	while len(players) > 1:
		player1 = players.pop()
		player2 = players.pop()
		match = create_game(users=[player1, player2], round=round_number, tournament=tournament, speed=tournament.speed, power_ups=tournament.power_ups)
		matches.append(match)

	if players:
		# Handle odd number of players: the last player gets a bye
		player1 = players.pop()
		match = create_game(users=player1, round=round_number, tournament=tournament, speed=tournament.speed, power_ups=tournament.power_ups)
		matches.append(match)

	return matches

def TournamentArchive(tournament, winner):
	tournament.winner = winner
	tournament.end_date = timezone.now()
	tournament.duration = tournament.end_date - tournament.start_date
	tournament.save()
	tournament.calculate_rankings()
	return

@csrf_exempt
def getTournamentRanking(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('tournament_id')
		user_id = data.get('user_id')
		if not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		if user_id:
			ranking = tournament.getUserRanking(user_id)
			return JsonResponse({'rank': ranking}, status=200)

		ranking = tournament.getRanking()
		return JsonResponse({'ranking': [{'id': player.player.id,
										 'username': player.player.username,
										 'wins': player.wins,
										 'rank': player.rank_position}
										 for player in ranking]
							}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def getTournamentPlayers(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('tournament_id')
		if not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		players = tournament.players.all()
		return JsonResponse({'players': [player.id for player in players]}, status=200)
	else:
		return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def getOwner(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('game_id')
		if not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		return JsonResponse({'owner_id': tournament.owner.id}, status=200)

# def updateOwner(tournament, players):
# 	if tournament.owner not in players:
# 		tournament.owner = players[0]
# 		tournament.save()


@csrf_exempt
def getTournamentInfo(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tournament_id = data.get('tournament_id')

		if not tournament_id:
			return JsonResponse({'message': 'Tournament ID is required.'}, status=400)

		try:
			tournament = Tournament.objects.get(id=tournament_id)
		except Tournament.DoesNotExist:
			return JsonResponse({'message': 'Tournament not found.'}, status=404)

		return JsonResponse({'n_players': tournament.n_players, 'joined': tournament.ready, 'name':tournament.name, 'finished': True if tournament.winner else False}, status=200)

def isPlayerBusy(player):
	tournaments = TournamentPlayer.objects.filter(player=player)
	for t in tournaments:
		if t.tournament.end_date == None:
			return t.tournament
	return None

@csrf_exempt
def getName(request):
	data = json.loads(request.body).get('tournament_id')
	try:
		tournament = Tournament.objects.get(id=data)
		return JsonResponse({'tournament_name':tournament.name}, status=200)
	except Tournament.DoesNotExist:
		return JsonResponse({'tournament_name':""}, status=404)
