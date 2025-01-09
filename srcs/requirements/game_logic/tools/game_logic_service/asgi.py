"""
ASGI config for pong project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# https://channels.readthedocs.io/en/latest/tutorial/part_2.html

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from game_logic.routing import websocket_patterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_logic_service.settings")

application = ProtocolTypeRouter(
	{
		"websocket": URLRouter(websocket_patterns)
	}
)
