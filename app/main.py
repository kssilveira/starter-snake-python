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

class Game(object):

  def __init__(self, board, width, height):
    self.board = board
    self.width = width
    self.height = height

  def adjacent(self, x, y):
    res = []
    for direction in DIRECTIONS:
      delta = DELTAS[direction]
      nx = x + delta['x']
      ny = y + delta['y']
      if nx >= 0 and nx < self.width and ny >= 0 and ny < self.height and self.board[ny][nx] == 0:
        res.append((direction, nx, ny))
    return res

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

    game = Game(board, width, height)

    # https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm

    distance = [[
      [[width * height * 999 for _ in range(width)] for _ in range(height)]
      for _ in range(width)] for _ in range(height)]

    for xs in range(width):
      for ys in range(height):
        distance[ys][xs][ys][xs] = 0
        for (_, nx, ny) in game.adjacent(xs, ys):
          distance[ys][xs][ny][nx] = 1

    for xm in range(width):
      for ym in range(height):
        for xs in range(width):
          for ys in range(height):
            for xe in range(width):
              for ye in range(height):
                distance[ys][xs][ye][xe] = min(
                  distance[ys][xs][ye][xe],
                  distance[ys][xs][ym][xm] + distance[ym][xm][ye][xe])

    # print 'distance'
    # pprint.pprint(distance)

    # import pdb; pdb.set_trace()
    # direction = random.choice(directions)

    res = game.adjacent(head['x'], head['y'])

    if len(res) > 0:
      direction, nx, ny = res[0]
      print 'direction', direction, 'nx', nx, 'ny', ny
      return move_response(direction)

    print 'no direction'
    return move_response('up')

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
