import websockets
import json
import logging
import os

logger = logging.getLogger('wsproxy')

CHAT_WS = os.getenv('CHAT_WS')+"?username=Tournament_Announcer"

chat_connection = None  # Persistent WebSocket connection

async def get_chat_connection():
	"""Gets or creates a persistent WebSocket connection to the chat service."""
	global chat_connection
	if chat_connection is None or not chat_connection.open:
		try:
			chat_connection = await websockets.connect(CHAT_WS)
			logger.info(f"Connected to Chat Service at {CHAT_WS}")
		except websockets.exceptions.InvalidURI as e:
			logger.error(f"Invalid URI for Chat Service: {CHAT_WS} - {e}")
			chat_connection = None
		except Exception as e:
			logger.error(f"Error connecting to Chat Service: {e}")
			chat_connection = None
	return chat_connection

async def send_to_chat(message):
	"""Sends a broadcast message to the chat service using the persistent connection."""
	connection = await get_chat_connection()
	if connection:
		try:
			chat_message = {
				"user": "Tournament_Announcer",
				"message": message,
			}
			await connection.send(json.dumps(chat_message))
			logger.info(f"Broadcasted to chat: {chat_message}")
		except websockets.exceptions.ConnectionClosed as e:
			logger.error(f"Connection to Chat Service closed: {e}")
			global chat_connection
			chat_connection = None
		except Exception as e:
			logger.error(f"Error sending message to Chat Service: {e}")
	else:
		logger.warning("No active connection to Chat Service.")
