#!/bin/bash
curl -kX POST https://localhost:8443/api/multi/join/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $TOKEN" \
-d "{\"game_id\": \"$1\"}"

SCRIPT_DIR="$(dirname "$(realpath "$0")")"

bash "$SCRIPT_DIR/join_my_game.sh" $1
