import os
import websockets
import logging
import json

logger = logging.getLogger('wsproxy')

# Environment variable for the game logic WebSocket URL
AI_WS = os.getenv('AI_WS')
ai_connection = None

async def get_ai_connection():
	"""Gets or creates a persistent WebSocket connection to ai opponent"""
	global ai_connection
	if ai_connection is None or not ai_connection.open:
		try:
			ai_connection = await websockets.connect(AI_WS)
			logger.info(f"Connected to AI at {AI_WS}")
		except websockets.exceptions.InvalidURI as e:
			logger.error(f"Invalid URI for AI: {AI_WS} - {e}")
			ai_connection = None
		except Exception as e:
			logger.error(f"Error connecting to AI: {e}")
			ai_connection = None
	return (ai_connection)

async def send_to_ai(gamestate, id):
	"""Sends a message to AI and receives a response."""
	global ai_connection
	connection = await get_ai_connection()
	data = {}
	data['gs'] = gamestate or {}
	data['id'] = id
	if connection:
		try:
			# Send the message to game_logic
			await connection.send(json.dumps(data))
			# logger.debug(f"Sent message to game_logic: {message}")

			# Wait for and parse the response
			response = await connection.recv()
			parsed_response = json.loads(response)
			# logger.debug(f"Received response from game_logic: {parsed_response}")
			return (parsed_response.get('input', {'ArrowUp': False, 'ArrowDown': False, 'w': False, 's': False, 'space': False}))

		except websockets.exceptions.ConnectionClosed as e:
			logger.error(f"Connection to AI closed: {e}")
			# Reset connection to trigger reconnection on the next call
			ai_connection = None
		except json.JSONDecodeError as e:
			logger.error(f"Failed to decode JSON from AI response: {e}")
		except Exception as e:
			logger.error(f"Error communicating with AI: {e}")
	else:
		logger.warning("No active connection to AI.")

	return ({"message": "error", "error": "Failed to communicate with AI"})
