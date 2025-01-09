import os
from django.core.asgi import get_asgi_application

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_service.settings')

# Initialize Django ASGI application first, before importing routing or any Django-specific modules
django_asgi_app = get_asgi_application()

# Now, import Channels-related modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from wsproxy.routing import websocket_urlpatterns

# Define the ASGI application with routing for HTTP and WebSocket protocols
application = ProtocolTypeRouter({
	"http": django_asgi_app,
	"websocket": AuthMiddlewareStack(
		URLRouter(
			websocket_urlpatterns
		)
	),
})

