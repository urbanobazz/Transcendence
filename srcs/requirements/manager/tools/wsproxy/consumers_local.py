from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
import random
from .umc_connection import validate_game, archive_game
from .glc_connection import send_to_glc, format_message
from .ai_connection import send_to_ai
from urllib.parse import parse_qs
from .live_game import LiveGame
import logging
import os

TICK_RATE = float(
	os.getenv('TICK_RATE', '0.05')
)  # Defines the game's tick rate, controlling the frequency of updates
WINNING_SCORE = 5  # Number of points needed to win the game
logger = logging.getLogger('wsproxy')


class LocalPongConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		self.active = 1
		self.game = LiveGame("local")
		self.r_score = self.l_score = 0
		query_string = self.scope["query_string"].decode()
		query_params = parse_qs(query_string)
		self.game_speed = query_params.get("game_speed", [1])[0]
		self.power_ups = query_params.get("power_ups", [True])[0]
		await self.accept()
		await self.send_start()
		asyncio.create_task(self.local_loop())

	async def receive(self, text_data):
		"""Handles incoming messages (inputs) from the client."""
		data = json.loads(text_data)
		self.game.inputs = data.get(
			'input', {
				'ArrowUp': False,
				'ArrowDown': False,
				'w': False,
				's': False,
				'space': False
			})

	async def disconnect(self, close_code):
		self.active = 0
	
	async def send_start(self):
		logger.debug("starting game now")

		await self.send(text_data=json.dumps({
			"message": "start_game",
		}))

	async def local_loop(self):
		self.message = ""
		while self.active:
			await asyncio.sleep(TICK_RATE)
			response = await send_to_glc(format_message(self.game.inputs if self.game else None, self.game.state if self.game else None, self.game_speed, self.power_ups))
			self.game.inputs = []
			self.message = response.get('message', 'update')
			self.game.state = response.get('gs', {})
			if (self.message == 'left'):
				self.l_score += 1
				if (self.l_score == WINNING_SCORE):
					self.active = 0
					self.message = 'l_win'
			elif (self.message == 'right'):
				self.r_score += 1
				if (self.r_score == WINNING_SCORE):
					self.active = 0
					self.message = 'r_win'
			self.game.state['rpad']['score'] = self.r_score
			self.game.state['lpad']['score'] = self.l_score
			await self.send(text_data=json.dumps({
				'gs': self.game.state,
				'message': self.message
			}))
		self.close()


class AiPongConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		self.active = 1
		self.game = LiveGame("ai")
		self.r_score = self.l_score = 0
		query_string = self.scope["query_string"].decode()
		query_params = parse_qs(query_string)
		self.game_speed = query_params.get("game_speed", [1])[0]
		self.power_ups = query_params.get("power_ups", [True])[0]
		await self.accept()
		await self.send_start()
		asyncio.create_task(self.local_loop())

	async def receive(self, text_data):
		"""Handles incoming messages (inputs) from the client."""
		data = json.loads(text_data)
		input_data = data.get(
			'input', {
				'ArrowUp': False,
				'ArrowDown': False,
				'w': False,
				's': False,
				'space': False
			})
		self.game.inputs['w'] = input_data.get('w') | input_data.get('ArrowUp')
		self.game.inputs['s'] = input_data.get('s') | input_data.get('ArrowDown')

	async def disconnect(self, close_code):
		self.active = 0
	
	async def send_start(self):
		logger.debug("starting AI game now")

		await self.send(text_data=json.dumps({
			"message": "start_game",
		}))


	async def local_loop(self):
		self.message = ""
		while self.active:
			await asyncio.sleep(TICK_RATE)
			# send GS to AI
			if self.game:
				ai_input = await send_to_ai(
					self.game.state,
					self.scope['url_route']['kwargs']['game_id'])
			else:
				ai_input = await send_to_ai(None, '')
			self.game.inputs['ArrowUp'] = ai_input.get('ArrowUp')
			self.game.inputs['ArrowDown'] = ai_input.get('ArrowDown')
			response = await send_to_glc(format_message(self.game.inputs, self.game.state if self.game else None, self.game_speed, self.power_ups))
			self.game.inputs = {}
			self.message = response.get('message', 'update')
			self.game.state = response.get('gs', {})
			logger.info(f"reponse.get('gs') {self.game.state}")
			if (self.message == 'left'):
				self.l_score += 1
				if (self.l_score == WINNING_SCORE):
					self.active = 0
					self.message = 'l_win'
			elif (self.message == 'right'):
				self.r_score += 1
				if (self.r_score == WINNING_SCORE):
					self.active = 0
					self.message = 'r_win'
			self.game.state['rpad']['score'] = self.r_score
			self.game.state['lpad']['score'] = self.l_score
			await self.send(text_data=json.dumps({
				'gs': self.game.state,
				'message': self.message
			}))
		self.close()
