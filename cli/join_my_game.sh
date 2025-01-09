#!/bin/bash

# Check if PLAYER_ID is set
if [ -z "$PLAYER_ID" ]; then
	echo "PLAYER_ID is not set. Exiting."
	exit 1
fi

# Start websocat in the background with a named pipe for input
PIPE="/tmp/websocket_input_pipe"
mkfifo "$PIPE"
tail -f "$PIPE" | websocat --insecure --no-close "wss://localhost:8443/ws/pong/$1/?player_id=$PLAYER_ID" > /dev/null &
WS_PID=$!

# Cleanup function
cleanup() {
	stty sane  # Restore terminal settings
	kill $WS_PID 2>/dev/null
	rm -f "$PIPE"  # Remove the named pipe
}
trap cleanup EXIT

# Set terminal to raw mode
stty -icanon -echo

echo "Press 'w' for ArrowUp, 's' for ArrowDown, 'q' to quit."

# Input loop
while true; do
	read -n 1 key  # Read a single keypress
	case "$key" in
		w)
			echo "send: UP"
			echo '{"message":"input","input":{"ArrowUp":true,"ArrowDown":false,"w":false,"s":false,"space":false}}' > "$PIPE"
			;;
		s)
			echo "send: DOWN"
			echo '{"message":"input","input":{"ArrowUp":false,"ArrowDown":true,"w":false,"s":false,"space":false}}' > "$PIPE"
			;;
		q)
			echo "Exiting..."
			break
			;;
		*)
			echo "Unknown key: $key"
			;;
	esac
done

cleanup
