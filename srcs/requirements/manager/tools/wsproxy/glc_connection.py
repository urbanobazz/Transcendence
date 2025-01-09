import json
import asyncio
import websockets
import os
import logging

logger = logging.getLogger('wsproxy')
send_lock = asyncio.Lock()  # Lock for managing concurrent WebSocket requests

# Environment variable for the game logic WebSocket URL
GAME_LOGIC_WS = os.getenv('GAME_LOGIC_WS')
glc_connection = None  # Persistent connection to game logic container

def format_message(input_data, gs, game_speed, power_ups):
	"""Formats the message to be sent to the game logic container."""
	formatted_message = {
		"input": input_data or {'ArrowUp': False, 'ArrowDown': False, 'w': False, 's': False, 'space': False},
		"gs": gs or {},
		"speed": game_speed or 1,
		"powerups": power_ups or True
	}
	return formatted_message

async def get_glc_connection():
	"""Gets or creates a persistent WebSocket connection to game_logic."""
	global glc_connection
	if glc_connection is None or not glc_connection.open:
		try:
			glc_connection = await websockets.connect(GAME_LOGIC_WS)
			logger.info(f"Connected to GLC at {GAME_LOGIC_WS}")
		except websockets.exceptions.InvalidURI as e:
			logger.error(f"Invalid URI for GLC: {GAME_LOGIC_WS} - {e}")
			glc_connection = None
		except Exception as e:
			logger.error(f"Error connecting to GLC: {e}")
			glc_connection = None
	return glc_connection

async def send_to_glc(message):
	"""Sends a message to game_logic and receives a response."""
	connection = await get_glc_connection()
	if connection:
		# Use asyncio.Lock to prevent concurrent access to the WebSocket connection
		async with send_lock:
			try:
				await connection.send(json.dumps(message))
				# logger.debug(f"Sent message to game_logic: {message}")

				# Wait for and parse the response
				response = await connection.recv()
				parsed_response = json.loads(response)
				# logger.debug(f"Received response from game_logic: {parsed_response}")
				return parsed_response

			except websockets.exceptions.ConnectionClosed as e:
				logger.error(f"Connection to GLC closed: {e}")
				# Reset connection to trigger reconnection on the next call
				global glc_connection
				glc_connection = None
			except json.JSONDecodeError as e:
				logger.error(f"Failed to decode JSON from GLC response: {e}")
			except Exception as e:
				logger.error(f"Error communicating with GLC: {e}")
	else:
		logger.warning("No active connection to GLC.")

	return {"message": "error", "error": "Failed to communicate with game_logic"}
