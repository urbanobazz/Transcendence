import json
import random
import os

# Game constants - Consider moving to environment variables or configuration file
PSPEED = int(os.getenv('PADDLE_SPEED', '8'))
BSPEED = int(os.getenv('BALL_SPEED', '8'))
GRID = int(os.getenv('GRID_SIZE', '15'))
PHEIGHT = int(os.getenv('PADDLE_HEIGHT', str(GRID * 4)))
CHEIGHT = int(os.getenv('CANVAS_HEIGHT', '450'))
CWIDTH = int(os.getenv('CANVAS_WIDTH', '800'))
MAXPADY = CHEIGHT - GRID - PHEIGHT
POWERUPS = ['psmall', 'plarge', 'invers']

# Initialize game state
def init_game(bar=0, type=None, speed=1):
	"""Initializes a new game state."""
	if not type:
		type = random.choice(POWERUPS)
	return {
		'ball': {
			'x': CWIDTH / 2,
			'y': CHEIGHT / 2,
			'width': GRID,
			'height': GRID,
			'dx': random.choice([-BSPEED, BSPEED]),
			'dy': random.uniform(-BSPEED + 1, BSPEED - 1),
			'spd': BSPEED * speed
		},
		'lpad': {
			'x': GRID * 2,
			'y': CHEIGHT / 2 - PHEIGHT / 2,
			'width': GRID,
			'height': PHEIGHT,
			'dy': 0
		},
		'rpad': {
			'x': CWIDTH - GRID * 3,
			'y': CHEIGHT / 2 - PHEIGHT / 2,
			'width': GRID,
			'height': PHEIGHT,
			'dy': 0
		},
		'powerups': {
			'bar': bar,
			'type': type,
			'active': 0
		}
	}

# Check for collision between ball and paddle
def collides(ball, paddle):
	return (ball['x'] < paddle['x'] + paddle['width'] and
			ball['x'] + ball['width'] > paddle['x'] and
			ball['y'] < paddle['y'] + paddle['height'] and
			ball['y'] + ball['height'] > paddle['y'])

# Clamp paddle position within canvas bounds
def clamp_paddle(paddle):
	paddle['y'] = max(GRID, min(paddle['y'], MAXPADY))

# Update paddle movement based on key states
def update_paddles(lpad, rpad, key_states, invers, speed):
	"""Updates paddles based on current key states."""
	if speed < 1:
		speed = 1
	w = key_states.get('w', False)
	s = key_states.get('s', False)
	up = key_states.get('ArrowUp', False)
	down = key_states.get('ArrowDown', False)
	if invers == 1:
		w = key_states.get('s')
		s = key_states.get('w')
	elif invers == 2:
		up = key_states.get('ArrowDown')
		down = key_states.get('ArrowUp')
	if w and not s:
		lpad['dy'] = -PSPEED * speed
	elif s and not w:
		lpad['dy'] = PSPEED * speed
	else:
		lpad['dy'] = 0  # stop paddle if no or both keys are pressed

	if up and not down:
		rpad['dy'] = -PSPEED * speed
	elif down and not up:
		rpad['dy'] = PSPEED * speed
	else:
		rpad['dy'] = 0

def apply_powerups(gs, powerups):
	if not powerups:
		gs['powerups']['type'] = 'off'
		return (gs)
	if (gs['powerups']['bar'] > -100 and gs['powerups']['bar'] < 100):
		return (gs)
	side = 'rpad' if gs['powerups']['bar'] <= -100 else 'lpad'
	type = gs['powerups']['type']
	if (type == 'psmall'):
		enemy = 'lpad' if side == 'rpad' else 'rpad'
		gs[enemy]['height'] = PHEIGHT - 30
	elif (type == 'plarge'):
		gs[side]['height'] = PHEIGHT + 30
	elif (type == 'invers'):
		gs['powerups']['active'] = 1 if side == 'rpad' else 2

	gs['powerups']['bar'] = 0
	return (gs)

# Update game state
def update_game(key_states, gs, powerups, speed):
	"""Processes game input and updates the game state."""
	message = 'update'

	# Initialize game state if empty
	if not gs:
		return {'gs': init_game(speed=speed), 'message': message}

	ball_speed = gs['ball']['spd'] + (0.05 * speed)
	gs['ball']['spd'] = ball_speed
	ball = gs['ball']
	lpad = gs['lpad']
	rpad = gs['rpad']

	# Handle paddle movement
	update_paddles(lpad, rpad, key_states, gs['powerups']['active'], speed)

	# Update paddle positions and clamp to boundaries
	lpad['y'] += lpad['dy']
	rpad['y'] += rpad['dy']
	clamp_paddle(lpad)
	clamp_paddle(rpad)

	# Update ball position
	ball['x'] += ball['dx']
	ball['y'] += ball['dy']

	# Ball collision with top and bottom walls
	if ball['y'] < GRID:
		ball['y'] = GRID
		ball['dy'] *= -1
	elif ball['y'] + ball['height'] > CHEIGHT - GRID:
		ball['y'] = CHEIGHT - GRID - ball['height']
		ball['dy'] *= -1

	# Check for paddle collisions
	if collides(ball, lpad):
		ball['dx'] = ball_speed
		ball['x'] = lpad['x'] + lpad['width']
		ball['dy'] += (lpad['dy']/2)
		gs['powerups']['bar'] += (ball_speed * 1.2)
	elif collides(ball, rpad):
		ball['dx'] = -ball_speed
		ball['x'] = rpad['x'] - ball['width']
		ball['dy'] += (rpad['dy']/2)
		gs['powerups']['bar'] -= (ball_speed * 1.2)

	# Check for scoring
	if ball['x'] < GRID:
		message = 'right'
		gs['powerups']['bar'] -= 30
		gs = init_game(speed=speed, bar=gs['powerups']['bar'], type=gs['powerups']['type'])
	elif ball['x'] > CWIDTH - GRID:
		message = 'left'
		gs['powerups']['bar'] += 30
		gs = init_game(speed=speed, bar=gs['powerups']['bar'], type=gs['powerups']['type'])
	else:
		gs['lpad'] = lpad
		gs['rpad'] = rpad
		gs['ball'] = ball

	# Return the updated game state and message

	gs = apply_powerups(gs, powerups)
	return {'gs': gs, 'message': message}
