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

DEBUG = False

class Game(object):

  def __init__(self, data, exclude_heads_of_other_snakes):
    board_data = data['board']

    self.height = board_data['height']
    self.width = board_data['width']
    self.food = board_data['food']

    self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]

    you = data['you']
    self.id = you['id']
    self.name = you['name']
    body = you['body']
    self.health = you['health']
    self.head = body[0]
    self.tail = body[-1]
    # for part in body[:-1]:
      # self.board[part['y']][part['x']] = 1

    snakes = board_data['snakes']
    for snake in snakes:
      # if snake['id'] == you['id']:
        # continue
      # for part in snake['body']:
      for part in snake['body'][:-1]:
        self.board[part['y']][part['x']] = 1
      if exclude_heads_of_other_snakes:
        if snake['id'] != self.id and len(snake['body']) >= len(body):
          head = snake['body'][0]
          for (_, nx, ny) in self.adjacent(head['x'], head['y']):
            self.board[ny][nx] = 1

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
    move_debug = [[NO_MOVE for _ in range(self.width)] for _ in range(self.height)]
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
      move_debug[y][x] = m[0]
      for (_, nx, ny) in self.adjacent(x, y):
        if res[ny][nx] == NO_DISTANCE:
          deque.append((nx, ny, d + 1, m))
    return res, move, move_debug

  def move_to_pos(self, x, y, moves):
    res = moves[y][x]
    print 'move_to_pos', 'x', x, 'y', y, 'res', res
    return res

  def move_to_max(self, distances, moves):
    maxdist = -1
    res = NO_MOVE
    for x in range(self.width):
      for y in range(self.height):
        if distances[y][x] > maxdist:
          maxdist = distances[y][x]
          res = moves[y][x]
    print 'move_to_max', 'maxdist', maxdist, 'res', res
    return res

  def move_to_food(self, distances, moves, tail_distances):
    res = NO_MOVE
    mindist = sys.maxint
    for food in self.food:
      x = food['x']
      y = food['y']
      dist = distances[y][x]
      if dist != NO_DISTANCE and (dist < mindist) and (
        (tail_distances[y][x] != NO_DISTANCE and
         tail_distances[y][x] >= 2)
         or self.health <= 25):
        mindist = dist
        res = moves[y][x]
    print 'move_to_food', 'mindist', mindist, 'res', res
    return res

def get_min_health(name):
  res = 100
  if "health_50" in name:
    res = 50
  print 'get_min_health', 'name', name, 'res', res
  return res

def print_debug(name, val):
  if DEBUG:
    print name
    pprint.pprint(val)

def run(data, exclude_heads_of_other_snakes):
    print 'exclude_heads_of_other_snakes', exclude_heads_of_other_snakes

    game = Game(data, exclude_heads_of_other_snakes)

    print_debug('board', game.board)

    # import pdb; pdb.set_trace()

    distances, moves, moves_debug = game.distances(game.head['x'], game.head['y'])

    print_debug('head_distances', distances)

    print_debug('moves_debug', moves_debug)

    tail_distances, _, _ = game.distances(game.tail['x'], game.tail['y'])

    print_debug('tail_distances', tail_distances)

    tails = [(_, game.tail['x'], game.tail['y'])] + game.adjacent(game.tail['x'], game.tail['y'])
    for (_, x, y) in tails:
      direction = game.move_to_pos(x, y, moves)
      if direction != NO_MOVE:
        break
    if direction == NO_MOVE:
      direction = game.move_to_max(distances, moves)
    if game.health <= get_min_health(game.name):
      food_direction = game.move_to_food(distances, moves, tail_distances)
      if food_direction != NO_MOVE:
        direction = food_direction
    print 'move_response', 'dir', direction

    return direction

# TODO
# - avoid food when too close to tail
# - maybe seek head of smaller snake
# - maybe predict future position of other snakes
#   - avoid getting locked
#   - lock others

@bottle.post('/move')
def move():
    data = bottle.request.json

    print "move()"
    # print(json.dumps(data))

    print_debug('data', data)

    print 'game id', data['game']['id']

    direction = run(data, exclude_heads_of_other_snakes=True)
    if direction == NO_MOVE:
      direction = run(data, exclude_heads_of_other_snakes=False)
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
