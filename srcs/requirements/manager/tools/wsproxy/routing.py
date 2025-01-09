from django.urls import path, re_path
from . import consumers
from . import consumers_local
from . import consumers_tour

websocket_urlpatterns = [ re_path(r'ws/pong/(?P<game_id>G-\w+)/$', consumers.PongConsumer.as_asgi()),
       re_path(r'ws/pong/(?P<game_id>LG-\w+)/$', consumers_local.LocalPongConsumer.as_asgi()),
       re_path(r'ws/pong/(?P<game_id>GAI-\w+)/$', consumers_local.AiPongConsumer.as_asgi()),
       re_path(r'ws/pong/(?P<game_id>T-\w+)/$', consumers_tour.TournamentConsumer.as_asgi())]
