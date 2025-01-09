"""
ASGI config for ai_service project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from ai_enemy.routing import websocket_patterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_service.settings')

application = ProtocolTypeRouter(
	{
		"websocket": URLRouter(websocket_patterns)
	}
)
