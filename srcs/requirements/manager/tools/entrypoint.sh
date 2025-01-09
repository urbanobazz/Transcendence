#!/bin/bash
# Start Gunicorn for serving the Django API on port 8001
gunicorn manager_service.wsgi:application --bind 0.0.0.0:8001 &
# Start Daphne for serving WebSocket connections on port 8002
daphne -b 0.0.0.0 -p 8002 manager_service.asgi:application
