from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
from .umc_connection import validate_game, archive_game
from .glc_connection import send_to_glc, format_message
from .live_game import LiveGame
from urllib.parse import parse_qs
import logging
import os
from django.conf import settings
import requests

TICK_RATE = float(os.getenv('TICK_RATE', '0.05'))
WINNING_SCORE = 5
logger = logging.getLogger('wsproxy')

class PongConsumer(AsyncWebsocketConsumer):

	async def init_game(self, game_id):
		tmp_game = validate_game(game_id)
		logger.info(f"Validating game {game_id} with UMC: {tmp_game}")
		query_string = self.scope["query_string"].decode()
		query_params = parse_qs(query_string)
		self.player_id = query_params.get("player_id", [None])[0]
		self.game_speed = float(tmp_game['speed'])
		if tmp_game['power_ups']:
			self.power_ups = 'true'
		else:
			self.power_ups = 'false'
		print(f"powerups {self.power_ups}, speed {self.game_speed}")
		if tmp_game['message'] != 'valid' and self.player_id not in [tmp_game['p1'], tmp_game['p2']]:
			logger.error(f"Game validation failed: {tmp_game['message']}. Connection rejected.")
			return False
		self.game = LiveGame.from_cache_or_create(game_id)
		self.game.save_to_cache()
		if not self.game.add_player(self.player_id):
			logger.warning(f"Cannot add player {self.player_id}; both slots are occupied.")
			return False
		logger.info(f"Added player {self.player_id} to game {self.game.to_dict()}.")
		return True

	async def connect(self):
		game_id = self.scope["url_route"]["kwargs"]["game_id"]
		# Retrieve game details and validate with user management service (UMC)
		if not await self.init_game(game_id):
			await self.close()
			return
		# Add player to the communication group for the game and accept the WebSocket connection
		await self.channel_layer.group_add(f"game_{self.game.id}", self.channel_name)
		await self.accept()
		# Start game if both players are ready, otherwise notify client to wait
		await self.start_game_if_ready()

	async def start_game_if_ready(self):
		"""Waits for a second player to join and initiates the game loop when both are ready."""

		logger.info(f"starting game for player {self.player_id}, game: {self.game.to_dict()}")
		# Loop to wait for both players to connect
		while not self.game.check_ready():
			logger.info(f"player {self.player_id} waiting, p1: {self.game.p1}, p2: {self.game.p2}")
			try:
				await self.send(
					text_data=json.dumps({"message": "waiting_for_player"}))
			except Exception as e:
				logger.warning(f"Failed to send waiting message: {e}")
			await self.send(text_data=json.dumps({"message": "waiting_for_player"}))  # Notify client to wait // this should theoretically use the async lock but probably we're fine
			await asyncio.sleep(0.5)  # Brief pause before rechecking

		# Request initial game state from game logic (GLC) and start game loop
		logger.info(f"player {self.player_id} starting game")
		await self.send_start()
		response = await send_to_glc(format_message(None, None, self.game_speed, self.power_ups))
		self.game.message = response.get('message', 'update')  # Set initial message
		self.game.state = response['gs']  # Set initial game state
		self.game.save_to_cache()  # Save initial state to cache
		asyncio.create_task(
			self.game_loop())  # Start the game loop as a background task

	async def disconnect(self, close_code):
		"""Handles player disconnection and archives the game state."""
		logger.info(f"Player {self.player_id} disconnected from game {self.game.id}.")
		# Check if game ended / there is a winner
		self.game.refresh_from_cache()
		if self.game.message in [self.game.p1.id, self.game.p2.id] or self.game.cancelled:
			return
		# Else set state and scores
		self.game.p1.score = WINNING_SCORE if self.player_id == self.game.p2.id else 0
		self.game.p2.score = WINNING_SCORE if self.player_id == self.game.p1.id else 0
		self.game.state['lpad']['score'] = self.game.p1.score
		self.game.state['rpad']['score'] = self.game.p2.score
		self.game.cancelled = True
		self.game.message = 'cancelled'
		self.game.save_to_cache()


	async def receive(self, text_data):
		"""Handles incoming messages (inputs) from the client."""

		# Refresh the game state from cache to ensure consistency
		self.game.refresh_from_cache()

		# Parse the incoming data as JSON and extract message type
		data = json.loads(text_data)
		message = data.get('message')

		if message == 'input':
			# Handle input based on player ID and combine directional inputs
			input_data = data.get(
				'input', {
					'ArrowUp': False,
					'ArrowDown': False,
					'w': False,
					's': False,
				})
			# Initialize keys for this player if not already set
			if self.game.p1.id == self.player_id:
				self.game.inputs['w'] = input_data.get('w') | input_data.get('ArrowUp')
				self.game.inputs['s'] = input_data.get('s') | input_data.get('ArrowDown')
			elif self.game.p2.id == self.player_id:
				self.game.inputs['ArrowUp'] = input_data.get('w') | input_data.get('ArrowUp')
				self.game.inputs['ArrowDown'] = input_data.get('s') | input_data.get('ArrowDown')
			# Save updated input state to cache
			self.game.save_to_cache()
			# logger.info(f"Received input from {self.player_id}: {input_data}")

	async def send_start(self):

		logger.debug("starting game now")
		data = {"user_id": self.game.p1.id,}
		response_p1 = requests.post(
			f"{settings.USER_MANAGEMENT}/user/validate/", json=data)

		data = {"user_id": self.game.p2.id,}
		response_p2 = requests.post(f"{settings.USER_MANAGEMENT}/user/validate/", json=data)

		await self.send(text_data=json.dumps({
			"message": "start_game",
			"p1": response_p1.json(),
			"p2": response_p2.json()
		}))

	def update_score(self, player):
		player.score += 1
		self.game.state['lpad']['score'] = self.game.p1.score
		self.game.state['rpad']['score'] = self.game.p2.score
		self.game.save_to_cache()
		logger.info(
			f"{player.id} scored. The score is {self.game.p1.score} : {self.game.p2.score}."
		)

	async def game_loop(self):
		"""Main game loop to manage ticks, process inputs, and broadcast the game state."""
		if self.game.p1.id == self.player_id:
			while await self.forward_tick():
				await asyncio.sleep(TICK_RATE)
		else:
			while (not self.game.cancelled and self.game.message in ['right', 'left', 'update']):
				await asyncio.sleep(TICK_RATE)
			await self.close_connection()

	async def forward_tick(self):
		"""Processes all inputs in the queue and updates the game state."""
		# Refresh game state from cache to capture the latest data
		self.game.refresh_from_cache()
		if self.game.cancelled:
			await self.close_connection()
			return False
		response = await send_to_glc(
			format_message(self.game.inputs, self.game.state, self.game_speed, self.power_ups))
		self.game.message = response.get('message', 'update')
		self.game.state = response.get('gs', {})
		self.game.save_to_cache()
		if self.game.message in ['left', 'right']:
			scorer = self.game.p1 if self.game.message == 'left' else self.game.p2
			self.update_score(scorer)
			if scorer.score >= WINNING_SCORE:
				await self.close_connection()
				return False
		await self.send_game_update()
		return True

	async def send_game_update(self):
		"""Broadcasts the current game state to all connected clients."""
		self.game.refresh_from_cache()
		# Group send to all players connected to the game
		await self.channel_layer.group_send(
			f"game_{self.game.id}",
			{
				"type": "game_update",
				"message": {
					'gs': self.game.state,
					'message': self.game.message
				}  # Include game state and update message
			})

	async def game_update(self, event):
		"""Sends the game state update to the individual client."""
		await self.send(text_data=json.dumps(event["message"]))

	async def close_connection(self):
		"""Closes the WebSocket connection gracefully when the game ends."""

		logger.info(f"Closing connection for player {self.player_id} in game {self.game.id} - score {self.game.p1.score} : {self.game.p2.score}, message: {self.game.message}.")
		self.game.refresh_from_cache()
		if self.game.message in ['left', 'right']:
			self.game.message = self.game.p1.id if self.game.message == 'left' else self.game.p2.id
			self.game.save_to_cache()
		elif self.game.cancelled:
			self.game.message = 'cancelled'
		await self.send_game_update()
		archive_game(self.game)
		await asyncio.sleep(0.5)
		await self.close()
