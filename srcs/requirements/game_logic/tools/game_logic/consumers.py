import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .pong_math import update_game
import logging

logger = logging.getLogger('game_logic')

class PongConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		await self.accept()
		logger.info("WebSocket connection accepted.")

	async def disconnect(self, close_code):
		logger.info(f"WebSocket connection closed with code {close_code}.")
		await self.close()

	async def receive(self, text_data):
		# Try parsing the received JSON
		try:
			data = json.loads(text_data)
			gs = data.get('gs', {})
			powerups = data.get('powerups', True)
			if isinstance(powerups, str):
				powerups = powerups.lower() == 'true'
			speed = float(data.get('speed', 1))
			input = data.get('input', {})

		except json.JSONDecodeError:
			logger.error(f"Json error: {e}")
			return
		except ValueError as e:
			logger.error(f"Validation error: {e}")
			return
		try:
			# Process the game logic based on the message type.
			new_gs = update_game(input, gs, powerups, speed)
			await self.send(text_data=json.dumps(new_gs))
		except Exception as e:
			logger.error(f"Sending/updating error: {e}")
