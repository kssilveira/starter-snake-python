import json
import os
import pprint
import random

import bottle

from api import ping_response, start_response, move_response, end_response

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print "start()"
    print(json.dumps(data))

    color = "#00FF00"

    return start_response(color)


DIRECTIONS = ['up', 'down', 'left', 'right']

DELTAS = {
  'up'   : { 'x':  0, 'y': -1, },
  'down' : { 'x':  0, 'y': +1, },
  'left' : { 'x': -1, 'y':  0, },
  'right': { 'x': +1, 'y':  0, },
}

@bottle.post('/move')
def move():
    data = bottle.request.json

    """
    TODO: Using the data from the endpoint request object, your
            snake AI must choose a direction to move in.
    """
    print "move()"
    print(json.dumps(data))
    print 'data'
    pprint.pprint(data)

    board_data = data['board']
    height = board_data['height']
    width = board_data['width']

    board = [[0 for _ in range(width)] for _ in range(height)]

    you = data['you']
    body = you['body']
    head = body[0]
    for part in body:
      board[part['y']][part['x']] = 1

    print 'board'
    pprint.pprint(board)

    # import pdb; pdb.set_trace()
    # direction = random.choice(directions)

    for direction in DIRECTIONS:
      delta = DELTAS[direction]
      nx = head['x'] + delta['x']
      ny = head['y'] + delta['y']
      print 'direction', direction, 'nx', nx, 'ny', ny
      if nx >= 0 and nx < width and ny >= 0 and ny < height and board[ny][nx] == 0:
        return move_response(direction)

@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print "end()"
    print(json.dumps(data))

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
