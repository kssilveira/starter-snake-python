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

    previous_tails[data['you']['id']] = []

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

previous_tails = {}

class Game(object):

  def __init__(self, data, exclude_heads_of_other_snakes):
    board_data = data['board']

    self.height = board_data['height']
    self.width = board_data['width']
    self.food = board_data['food']

    self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]

    you = data['you']
    self.id = you['id']
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
        if snake['id'] != self.id:
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
      # print 'x', x, 'y', y, 'd', d
      # print 'res'
      # pprint.pprint(res)
      # import pdb; pdb.set_trace()
      for (_, nx, ny) in self.adjacent(x, y):
        if res[ny][nx] == NO_DISTANCE:
          deque.append((nx, ny, d + 1, m))
    return res, move, move_debug

  def move_to_free(self):
    res = self.adjacent(self.head['x'], self.head['y'])
    if len(res) > 0:
      direction, nx, ny = res[0]
      print 'direction', direction, 'nx', nx, 'ny', ny
      return direction
    print 'no direction'
    return 'up'

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
      if dist != NO_DISTANCE and (dist < mindist) and tail_distances[y][x] != NO_DISTANCE:
        mindist = dist
        res = moves[y][x]
    print 'move_to_food', 'mindist', mindist, 'res', res
    return res

def run(data, exclude_heads_of_other_snakes):
    print 'exclude_heads_of_other_snakes', exclude_heads_of_other_snakes

    game = Game(data, exclude_heads_of_other_snakes)

    print 'previous_tails', previous_tails
    print 'previous_tails[id]', previous_tails[game.id]

    print 'board'
    pprint.pprint(game.board)

    # import pdb; pdb.set_trace()

    distances, moves, moves_debug = game.distances(game.head['x'], game.head['y'])

    print 'head_distances'
    pprint.pprint(distances)

    print 'moves_debug'
    pprint.pprint(moves_debug)

    tail_distances, _, _ = game.distances(game.tail['x'], game.tail['y'])

    print 'tail_distances'
    pprint.pprint(tail_distances)

    # print 'moves'
    # pprint.pprint(moves)

    previous_tails[game.id].append(game.tail)
    if len(previous_tails[game.id]) > 10:
      previous_tails[game.id] = previous_tails[game.id][-10:]

    for tail in reversed(previous_tails[game.id]):
      direction = game.move_to_pos(tail['x'], tail['y'], moves)
      if direction != NO_MOVE:
        break
    if direction == NO_MOVE and not exclude_heads_of_other_snakes:
      direction = game.move_to_max(distances, moves)
    if game.health <= 50:
      food_direction = game.move_to_food(distances, moves, tail_distances)
      if food_direction != NO_MOVE:
        direction = food_direction
    print 'move_response', 'dir', direction
    return direction

@bottle.post('/move')
def move():
    data = bottle.request.json

    print "move()"
    # print(json.dumps(data))
    print 'data'
    pprint.pprint(data)

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
