#!/bin/bash
curl -kX POST https://localhost:8443/api/multi/create/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $TOKEN" \
-d "{\"game_name\": \"$1\", \"n_players\": \"2\", \"game_speed\": \"1\", \"power_ups\": \"True\"}"
