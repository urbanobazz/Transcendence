from django.urls import path
from . import consumers

websocket_patterns = [
	path('ws/pong/', consumers.PongConsumer.as_asgi()),  # Add a trailing slash and more specific URL
	path('ws/pong', consumers.PongConsumer.as_asgi()),  # Add a trailing slash and more specific URL
]
