# consumers_tour.py
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import json, requests, logging, random, asyncio
from .chat_connection import send_to_chat
from .umc_connection import get_user_name, get_tournament_name

logger = logging.getLogger('wsproxy')

class TournamentConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		# Extract game_id from the URL and create a unique group name
		self.game_id = self.scope['url_route']['kwargs']['game_id']
		self.user_id = self.scope["query_string"].decode().split("user_id=")[-1]
		self.group_name = f'tournament_{self.game_id}'
		self.name = get_tournament_name(self.game_id)
		self.user_name = get_user_name(self.user_id)

		# Add this WebSocket connection to the group
		await self.channel_layer.group_add(self.group_name, self.channel_name)

		# Accept the WebSocket connection
		await self.accept()
		await send_to_chat(f"{self.user_name} joined tournament {self.name} - head over to the tournament tab to battle them!")

	async def disconnect(self, close_code):
		await send_to_chat(f"{self.user_name} dropped out from tournament {self.name} - head over to the tournament tab to battle them!")
		# Remove the WebSocket connection from the group
		await self.channel_layer.group_discard(self.group_name,
											self.channel_name)

	async def receive(self, text_data):
		data = json.loads(text_data)
		action = data.get('action')

		if action == 'userReady':
			data = {"tournament_id": self.game_id,}

			response = requests.post(
			f"{settings.USER_MANAGEMENT}/tournaments/run/", json=data
			)
			logger.info(f"Tournament run endpoint response{response.json()}")
			await self.forward_response(response.json())

		elif action == 'finished':
			data = {"tournament_id": self.game_id,}

			response = requests.post(
			f"{settings.USER_MANAGEMENT}/tournaments/run/", json=data
			)
			await self.forward_response(response.json())

	async def forward_response(self, response):
		# Send response to all users in the group
		await self.channel_layer.group_send(
			self.group_name, {
				'type': 'user_response',
				'message': 'Forwarded response from other client',
				'response': response
			})

	# This method will be called on each client when a "user_response" message is broadcast
	async def user_response(self, event):
		message = event['message']
		response = event['response']

		if 'winner' not in response or not response['winner']:
			logger.info(f"Tournament running, response from API {response}")
			if 'matches' not in response or not response['matches']: # Check if 'matches' exists and is not empty
				logger.info("No matches found or tournament hasn't started yet.")
				await self.send(text_data=json.dumps({
						'action': 'waiting',
						'message': 'Not enough participants!',
					}))
				return

			for match in response['matches']:
				if self.user_id == match['p1']['id'] or self.user_id == match['p2']['id']:

					opponent = match['p2'] if self.user_id == match['p1']['id'] else match['p1']

					asyncio.sleep(random.randint(1, 5)/10) # avoid race condition on filling p1 slot, this is hacky but should work
					# Send the message to WebSocket
					await self.send(text_data=json.dumps({
						'action': 'tournamentStarted',
						'message': 'Tournament has started!',
						'game_id': match['id'],
						'user_id': self.user_id,
						'opponent_name': opponent['name'],
						'opponent_id': opponent['id'],

					}))

		elif 'winner' in response or response['winner']:
			logger.info(f"Tournament finished, response from API {response}")
			await self.send(text_data=json.dumps({
				'action': 'finished',
				'message': 'Tournament has finished!',
				'winner': response['winner'],
				'name' : response['name'],
			}))
			if self.user_name == response['winner']:
				send_to_chat(f"{response['name']} won tournament {self.name} - what a champ!")

		else:
			await self.send(text_data=json.dumps({
				'action': 'error',
				'message': 'Error in fetching tournament',
			}))

