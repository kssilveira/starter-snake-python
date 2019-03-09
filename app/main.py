import collections
import json
import os
import pprint
import random
import sys

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

NO_DISTANCE = -1
NO_MOVE = '?'

class Game(object):

  def __init__(self, data):
    board_data = data['board']

    self.height = board_data['height']
    self.width = board_data['width']
    self.food = board_data['food']

    self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]

    you = data['you']
    body = you['body']
    self.health = you['health']
    self.head = body[0]
    self.tail = body[-1]
    for part in body[:-1]:
      self.board[part['y']][part['x']] = 1

  def adjacent(self, x, y):
    res = []
    for direction in DIRECTIONS:
      delta = DELTAS[direction]
      nx = x + delta['x']
      ny = y + delta['y']
      if nx >= 0 and nx < self.width and ny >= 0 and ny < self.height and self.board[ny][nx] == 0:
        res.append((direction, nx, ny))
    return res

  def distances(self, x, y):
    res = [[NO_DISTANCE for _ in range(self.width)] for _ in range(self.height)]
    move = [[NO_MOVE for _ in range(self.width)] for _ in range(self.height)]
    # Flood fill.
    res[y][x] = 0
    deque = collections.deque()
    for (m, nx, ny) in self.adjacent(x, y):
      deque.append((nx, ny, 1, m))
    while deque:
      (x, y, d, m) = deque.popleft()
      if res[y][x] != NO_DISTANCE:
        continue
      res[y][x] = d
      move[y][x] = m
      # move[y][x] = m[0]
      # print 'x', x, 'y', y, 'd', d
      # print 'res'
      # pprint.pprint(res)
      # import pdb; pdb.set_trace()
      for (_, nx, ny) in self.adjacent(x, y):
        if res[ny][nx] == NO_DISTANCE:
          deque.append((nx, ny, d + 1, m))
    return res, move

  def move_to_free(self):
    res = self.adjacent(self.head['x'], self.head['y'])
    if len(res) > 0:
      direction, nx, ny = res[0]
      print 'direction', direction, 'nx', nx, 'ny', ny
      return direction
    print 'no direction'
    return 'up'

  def move_to_tail(self, moves):
    x = self.tail['x']
    y = self.tail['y']
    res = moves[y][x]
    print 'x', x, 'y', y, 'res', res
    return res

  def move_to_max(self, distances, moves):
    maxdist = -1
    res = NO_MOVE
    for x in range(self.width):
      for y in range(self.height):
        if distances[y][x] > maxdist:
          maxdist = distances[y][x]
          res = moves[y][x]
    return res

  def move_to_food(self, distances, moves):
    res = NO_MOVE
    mindist = sys.maxint
    for food in self.food:
      x = food['x']
      y = food['y']
      dist = distances[y][x]
      if dist != NO_DISTANCE and (dist < mindist):
        mindist = dist
        res = moves[y][x]
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

    game = Game(data)

    print 'board'
    pprint.pprint(game.board)

    # import pdb; pdb.set_trace()

    distances, moves = game.distances(game.head['x'], game.head['y'])

    print 'distances'
    pprint.pprint(distances)

    # print 'moves'
    # pprint.pprint(moves)

    direction = game.move_to_tail(moves)
    if direction == NO_MOVE:
      direction = game.move_to_max(distances, moves)
    if game.health <= 50:
      food_direction = game.move_to_food(distances, moves)
      if food_direction != NO_MOVE:
        direction = food_direction
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
