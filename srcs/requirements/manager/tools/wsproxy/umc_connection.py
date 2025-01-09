import json
import os
import logging
from datetime import datetime
from django.conf import settings
import requests

logger = logging.getLogger('wsproxy')

def validate_game(game_id):
	url = f"{settings.USER_MANAGEMENT}/multi/validate/"
	response = requests.post(url, json={"game_id": game_id})
	if response.status_code != 200:
		return {"message": f"Unexpected error: {response.status_code}"}
	data = response.json()
	if game_id != data.get("id"):
		return {"message": "invalid"}
	return {
		"message": "valid",
		"id": game_id,
		"p1": data.get("p1", "No player 1"),
		"p2": data.get("p2", "No player 2"),
		"speed": data.get("speed"),
		"power_ups": data.get("power_ups")
	}

def archive_game(game):
	url = f"{settings.USER_MANAGEMENT}/multi/archive/"
	payload = {
		"game_id": game.id,
		"end_date": datetime.now().isoformat(),
		"scores": {'score1': game.p1.score, 'score2': game.p2.score},
		"winner": game.p1.id if game.p1.score > game.p2.score else game.p2.id,
		"p1": game.p1.id,
		"p2": game.p2.id
	}
	response = requests.post(url, json=payload)
	return {"message": "Game archived successfully."} if response.status_code == 200 else {"message": f"Unexpected error: {response.status_code}"}

def get_tournament_name(tournament_id):
	url = f"{settings.USER_MANAGEMENT}/tournaments/getname/"
	response = requests.post(url, json={'tournament_id': tournament_id})
	if response.status_code != 200:
		return ""
	return response.json()['tournament_name']

def get_user_name(user_id):
	url = f"{settings.USER_MANAGEMENT}/user/validate/"
	response = requests.post(url, json={"user_id": user_id})
	if response.status_code != 200:
		return ""
	return response.json()['username']

