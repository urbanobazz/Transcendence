import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from pongchat import consumers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_manager.settings")

application = ProtocolTypeRouter({
	"http": get_asgi_application(),
	"websocket": AuthMiddlewareStack(
		URLRouter([
			path("ws/chat/", consumers.ChatRoomConsumer.as_asgi()),
		])
	),
})
