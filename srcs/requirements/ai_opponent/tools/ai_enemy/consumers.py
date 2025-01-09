import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .ai_logic import ai_response

logger = logging.getLogger('ai_opponent')

class AiConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		await self.accept()
		logger.info("WebSocket connection accepted.")

	async def disconnect(self, close_code):
		logger.info(f"WebSocket connection closed with code {close_code}.")
		await self.close()

	async def receive(self, text_data):
		# Try parsing the received JSON
		try:
			text_data_json = json.loads(text_data)
			# logger.debug(f"Received from manager:\n {text_data_json}")

		except json.JSONDecodeError:
			logger.error(f"Json error: {e}")
			return
		except ValueError as e:
			logger.error(f"Validation error: {e}")
			return
		
		response = ai_response(text_data_json)

		try:
			await self.send(text_data=json.dumps(response))
		except Exception as e:
			logger.error(f"Sending/updating error: {e}")
