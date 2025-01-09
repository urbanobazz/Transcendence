import logging
import os
from time import time

logger = logging.getLogger('ai_opponent')

CHEIGHT = int(os.getenv('CANVAS_HEIGHT', '450'))
CWIDTH = int(os.getenv('CANVAS_WIDTH', '800'))
GRID = int(os.getenv('GRID_SIZE', '15'))
PSPEED = int(os.getenv('PADDLE_SPEED', '8'))
games:dict = {}

# {'input': {'ArrowUp': False, 'ArrowDown': True, 'w': False, 's': False, 'space': False}}

def get_ball_ty(gamestate:dict) -> float:
	ball:dict = gamestate['ball']
	x:float = ball['x']
	y:float = ball['y']
	dx:float = ball['dx']
	dy:float = ball['dy']
	x_min:int = gamestate['lpad']['x'] + gamestate['lpad']['width']
	x_max:int = gamestate['rpad']['x'] - ball['width']
	y_min:int = GRID
	y_max = CHEIGHT - GRID - ball['height']

	while x < x_max:
		x += dx
		y += dy
		if y < y_min:
			y = y_min
			dy *= -1
		elif y > y_max:
			y = y_max
			dy *= -1
		if x < x_min:
			x = x_min
			dx *= -1
	return y + (ball['height'] / 2)

def generate_inputs(game:dict, invers = False) -> None:
	game['inputs'] = []
	to_move:float = get_ball_ty(game['gs']) - float(game['gs']['rpad']['y'] + (game['gs']['rpad']['height'] / 2))
	for i in range(int(abs(to_move) / float(PSPEED))):
		if to_move > 0 or (to_move < 0 and invers):
			game['inputs'].append({'ArrowUp': False, 'ArrowDown': True, 'w': False, 's': False, 'space': False})
		else:
			game['inputs'].append({'ArrowUp': True, 'ArrowDown': False, 'w': False, 's': False, 'space': False})
	if abs(to_move) > float(PSPEED):
		game['inputs'].append({'ArrowUp': True, 'ArrowDown': False, 'w': False, 's': False, 'space': False})

def ai_response(message:dict) -> dict:

	id:str = message.get('id', '')
	gamestate = message.get('gs', {})
	ball = gamestate.get('ball')
	pad = gamestate.get('rpad')
	power = gamestate.get('powerups')

	if not ball or not pad or not power or id == '' or len(gamestate) == 0:
		logger.error("Error in gamestate parsing")
		return {'input': {}}
	
	invers = power['type'] == 'invers' and power['active'] == 1

	if id not in games:
		games[id] = {
			'gs': gamestate,
			'time': time(),
			'inputs': []
		}
		generate_inputs(games[id], invers)
	elif time() - games[id]['time'] >= 1: # delay in seconds
		games[id]['time'] = time()
		games[id]['gs'] = gamestate
		generate_inputs(games[id], invers)

	inputs = {}
	if len(games[id]['inputs']) > 0:
		inputs = games[id]['inputs'].pop(0)
	return {'input': inputs}

