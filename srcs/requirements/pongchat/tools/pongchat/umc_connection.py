import json, requests
# import os
# import logging
# from datetime import datetime
from django.conf import settings

def validate_user(user_name):
	url = f"{settings.USER_MANAGEMENT}/user/validate/"
	response = requests.post(url, json={"username": user_name})
	if response.status_code != 200:
		return False
	return response.json()['id']

def create_multi(p1, p2):

	user1 = validate_user(p1)
	user2 = validate_user(p2)

	data = {
		"user_id": user1,
		"friend": user2,
		"is_ai": False,
		"game_name": f"{p1} VS {p2}"
	}
	response = requests.post(settings.USER_MANAGEMENT + "/chat/game/", json=data)

	res = response.json()
	return res['id']

def get_blocklist(username):
	user_id = validate_user(username)
	url = f"{settings.USER_MANAGEMENT}/friends/listblocked/"
	response = requests.post(url, json={"user_id": user_id})
	if response.status_code != 200:
		return []
	return [u['username'] for u in response.json()]




# def join_multi():

# 	if request.method == "POST":
# 		# Extract game_id and user_id from the request data
# 		user_id = request.user.user_id  # User's ID from the request context
# 		game_id = request.data.get(
# 			"game_id")  # Expecting "game_id" in POST body

# 		if not game_id:
# 			return JsonResponse({"error": "Missing game_id in request data"},
# 								status=400)

# 		# Prepare payload for user management service
# 		payload = {"user_id": user_id, "game_id": game_id}

# 		# Forward the request to the user management service
# 		response = requests.post(f"{settings.USER_MANAGEMENT}/multi/join/",
# 								 json=payload)

# 		# Return the response from the user management service
# 		return JsonResponse(data=response.json(),
# 							status=response.status_code,
# 							safe=False)



# def validate_game(game_id):
# 	url = f"{settings.USER_MANAGEMENT}/multi/validate/"
# 	response = requests.post(url, json={"game_id": game_id})
# 	if response.status_code != 200:
# 		return {"message": f"Unexpected error: {response.status_code}"}
# 	data = response.json()
# 	if game_id != data.get("id"):
# 		return {"message": "invalid"}
# 	return {
# 		"message": "valid",
# 		"id": game_id,
# 		"p1": data.get("p1", "No player 1"),
# 		"p2": data.get("p2", "No player 2"),
# 	}



# def archive_game(game):
# 	url = f"{settings.USER_MANAGEMENT}/multi/archive/"
# 	payload = {
# 		"game_id": game.id,
# 		"end_date": datetime.now().isoformat(),
# 		"scores": {'score1': game.p1.score, 'score2': game.p2.score},
# 		"winner": game.p1.id if game.p1.score > game.p2.score else game.p2.id,
# 		"p1": game.p1.id,
# 		"p2": game.p2.id
# 	}
# 	response = requests.post(url, json=payload)
# 	return {"message": "Game archived successfully."} if response.status_code == 200 else {"message": f"Unexpected error: {response.status_code}"}

