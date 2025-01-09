from django.urls import path
from . import consumers

websocket_patterns = [
	path('ws/default/', consumers.AiConsumer.as_asgi())
]
