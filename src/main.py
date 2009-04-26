# Copyright (c) 2009 Mike Tsao

# TODO
#
# - fire particles
# - smooth turret rotation
# - explosions and carcasses
# - drag new turrets from menu
# - sell/upgrade menu

from pygame.locals import *
from pymunk.vec2d import Vec2d
import math
import os
import pygame
import random
import sys
import time

SCREEN_SIZE_X = 480
SCREEN_SIZE_Y = 320
FPS = 60
ASSET_DIR = 'assets'
TRANSPARENCY_KEY_COLOR = (255, 0, 255)

FIELD_BACKGROUND_COLOR = (0, 192, 0)
DASH_BACKGROUND_COLOR = (128, 128, 128)
DASH_COLOR = (192, 192, 0)
BANNER_ALPHA = 192
BANNER_DURATION = 4000
BANNER_FADE_IN_END = 3750
BANNER_FADE_OUT_START = 1000

SPAWN_ENEMY = pygame.USEREVENT
BEGIN_LEVEL = pygame.USEREVENT + 1

def get_font(size):
  return pygame.font.Font(os.path.join(ASSET_DIR, 'surface_medium.otf'), size)

def load_sound(name):
  class NoneSound:
    def play(self): pass
  if not pygame.mixer or not pygame.mixer.get_init():
    return NoneSound()
  fullname = os.path.join(ASSET_DIR, name)
  try:
    sound = pygame.mixer.Sound(fullname)
  except pygame.error, message:
    print 'Cannot load sound:', fullname
    raise SystemExit, message
  return sound

class Base(pygame.sprite.Sprite):
  def __init__(self, position, game, is_exit=False):
    pygame.sprite.Sprite.__init__(self)
    self.game = game
    self.is_exit = is_exit
    self.image = pygame.image.load(os.path.join(ASSET_DIR, 'base.png'))
    self.rect = self.image.get_rect()
    self.position = position
    self.rect.center = position

  def update(self, dt):
    pass

class Wall(pygame.sprite.Sprite):
  def __init__(self, position, game):
    pygame.sprite.Sprite.__init__(self)
    self.game = game
    self.parent_group = game.environment_sprites
    self.image = pygame.image.load(os.path.join(ASSET_DIR, 'wall.png'))
    self.rect = self.image.get_rect()
    self.rect.center = position

  def update(self, dt):
    pass

class Attacker(pygame.sprite.Sprite):
  def __init__(self, position, game, image, sound_explosion,
               health, speed, value):
    pygame.sprite.Sprite.__init__(self)
    self.game = game
    self.parent_group = game.enemy_sprites
    self.image = image
    self.sound_explosion = sound_explosion
    self.rect = image.get_rect()
    self.original_image = self.image
    self.position = position
    self.rect.center = position
    self.game = game
    self.angle_degrees = 0
    self.starting_health = health * game.get_level_multiplier()
    self.health = self.starting_health
    self.speed = speed * game.get_level_multiplier()
    self.value = value
    
    self.recalculate_goal_position()

  def recalculate_goal_position(self):
    grid_position = self.game.grid.screen_to_grid(self.position)
    self.goal_grid_position = self.game.path_map.get(grid_position)
    if self.goal_grid_position:
      return
    path = self.game.grid.find_path(grid_position, self.game.exit_grid_pos)
    if path:
      self.game.path_map.add(path)
      self.goal_grid_position = self.game.path_map.get(grid_position)
      return
    print 'ERROR: attacker got stuck!'

  def die(self):
    self.game.kill_actor_sprite(self)
    self.game.notify_enemy_sprite_change()

  def inflict_damage(self, points):
    self.health -= points
    if self.health <= 0:
      self.sound_explosion.play()
      self.game.award_kill(self.value)
      self.die()

  def check_base_collision(self):
    base_collisions = pygame.sprite.spritecollide(self, self.game.bases,
                                                  False)
    for base in base_collisions:
      if base.is_exit:
        self.game.deduct_life()
        self.die()

  def get_goal_vector(self):
    grid_position = self.game.grid.screen_to_grid(self.position)
    if grid_position == self.goal_grid_position:
      self.recalculate_goal_position()
    vector = (Vec2d(self.game.grid.grid_to_screen(self.goal_grid_position)) - 
              Vec2d(self.rect.center))
    return vector.normalized()

  def update(self, dt):
    vector = self.get_goal_vector()
    self.angle_degrees = - vector.get_angle()
    self.position += vector * (self.speed * float(dt) / float(FPS))
    self.check_base_collision()
    collision_func = pygame.sprite.collide_circle_ratio(2.0)

    self.rect.center = self.position
    rotate = pygame.transform.rotate
    self.image = rotate(self.original_image, self.angle_degrees)

  def draw(self, surface):
    if self.health < self.starting_health:
      full_rect = pygame.Rect((self.rect.topleft), (self.rect.width, 2))
      rect = pygame.Rect((self.rect.topleft),
                         (self.rect.width * self.health / 
                          self.starting_health, 2))
      surface.fill((255, 0, 0), full_rect)
      surface.fill((0, 255, 0), rect)

class EasyAttacker(Attacker):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'attacker.png')
  SPEED = 2.0
  HEALTH = 20.0
  VALUE = 1.0
  
  image = None
  sound_explosion = None
  
  def __init__(self, position, game):
    if EasyAttacker.image is None:
      EasyAttacker.image = pygame.image.load(EasyAttacker.IMAGE_FILENAME)
    if EasyAttacker.sound_explosion is None:
      EasyAttacker.sound_explosion = load_sound('explosion.wav')
    Attacker.__init__(self, position, game,
                      EasyAttacker.image,
                      EasyAttacker.sound_explosion,
                      EasyAttacker.HEALTH,
                      EasyAttacker.SPEED,
                      EasyAttacker.VALUE)

class HardAttacker(Attacker):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'attacker.png')
  SPEED = 1.8
  HEALTH = 60.0
  VALUE = 1.0
  
  image = None
  sound_explosion = None
  
  def __init__(self, position, game):
    if HardAttacker.image is None:
      HardAttacker.image = pygame.image.load(HardAttacker.IMAGE_FILENAME)
    if HardAttacker.sound_explosion is None:
      HardAttacker.sound_explosion = load_sound('explosion.wav')
    Attacker.__init__(self, position, game,
                      HardAttacker.image,
                      HardAttacker.sound_explosion,
                      HardAttacker.HEALTH,
                      HardAttacker.SPEED,
                      HardAttacker.VALUE)

class Turret(pygame.sprite.Sprite):
  def __init__(self, position, game, image, sound_shot,
               fire_rate=1000.0,
               fire_ratio=2.0,
               damage_ability=5.0,
               cost=0.0,
               splash=False):
    pygame.sprite.Sprite.__init__(self)
    self.game = game
    self.parent_group = game.environment_sprites
    self.image = image
    self.sound_shot = sound_shot
    self.rect = image.get_rect()
    self.original_image = self.image
    self.position = position
    self.rect.center = position

    self.game = game
    self.angle_degrees = 0

    self.fire_countdown = random.randint(50, 500)
    self.fire_rate = fire_rate
    self.fire_ratio = fire_ratio
    self.damage_ability = damage_ability
    self.splash = splash # TODO
    self.value = int(cost * 0.8)

  def die(self):
    self.game.kill_actor_sprite(self)

  def check_enemy_collisions(self, dt):
    if self.fire_countdown > 0:
      self.fire_countdown -= dt
      return

    collision_func = pygame.sprite.collide_circle_ratio(self.fire_ratio)
    nearby_enemies = pygame.sprite.spritecollide(self,
                                                 self.game.enemy_sprites,
                                                 False,
                                                 collision_func)
    if len(nearby_enemies) > 0:
      enemy = nearby_enemies[0]
      self.fire_countdown = self.fire_rate
      self.sound_shot.play()
      enemy.inflict_damage(self.damage_ability)
      vector = (Vec2d(self.position) - Vec2d(enemy.position)).normalized()
      self.angle_degrees = - vector.get_angle()

  def update(self, dt):
    self.check_enemy_collisions(dt)
    rotate = pygame.transform.rotate
    self.image = rotate(self.original_image, self.angle_degrees)

class SmallTurret(Turret):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'turret.png')
  FIRE_RATE = 1000.0
  FIRE_RATIO = 2.0
  DAMAGE_ABILITY = 5.0
  COST = 3.0
  SPLASH = False
  
  image = None
  sound_shot = None
  
  def __init__(self, position, game):
    if SmallTurret.image is None:
      SmallTurret.image = pygame.image.load(SmallTurret.IMAGE_FILENAME)
    if SmallTurret.sound_shot is None:
      SmallTurret.sound_shot = load_sound('shot.wav')
    Turret.__init__(self, position, game, SmallTurret.image,
                    SmallTurret.sound_shot,
                    fire_rate=SmallTurret.FIRE_RATE,
                    fire_ratio=SmallTurret.FIRE_RATIO,
                    damage_ability=SmallTurret.DAMAGE_ABILITY,
                    cost=SmallTurret.COST,
                    splash=SmallTurret.SPLASH)

class BigTurret(Turret):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'turret2.png')
  FIRE_RATE = 500.0
  FIRE_RATIO = 3.0
  DAMAGE_ABILITY = 20.0
  COST = 10.0
  SPLASH = True
  
  image = None
  sound_shot = None
  
  def __init__(self, position, game):
    if BigTurret.image is None:
      BigTurret.image = pygame.image.load(BigTurret.IMAGE_FILENAME)
    if BigTurret.sound_shot is None:
      BigTurret.sound_shot = load_sound('shot.wav')
    Turret.__init__(self, position, game, BigTurret.image,
                    BigTurret.sound_shot,
                    fire_rate=BigTurret.FIRE_RATE,
                    fire_ratio=BigTurret.FIRE_RATIO,
                    damage_ability=BigTurret.DAMAGE_ABILITY,
                    cost=BigTurret.COST,
                    splash=BigTurret.SPLASH)

class PathMap(object):
  def __init__(self, coords):
    self.nexts = {}
    self.add(coords)

  def add(self, coords):
    for i in range(0, len(coords) - 1):
      self.nexts[coords[i]] = coords[i + 1]

  def get(self, pos):
    return self.nexts.get(pos, None)

class Grid(object):
  def __init__(self, col_count, row_count, tile_size):
    self.col_count = col_count
    self.row_count = row_count
    self.tile_size = tile_size
    self.tile_midpoint = tile_size / 2
    self.screen_x = col_count * tile_size
    self.screen_y = row_count * tile_size
    self.cells, self.open_count = self.init_array(col_count, row_count)

  def screen_to_grid(self, (x, y)):
    return int(x) / self.tile_size, int(y) / self.tile_size
  
  def grid_to_screen(self, (x, y)):
    return (x * self.tile_size + self.tile_midpoint,
            y * self.tile_size + self.tile_midpoint)
  
  def set_cell(self, col, row, contents):
    offset = self.get_cell_offset(col, row)
    if offset >= 0:
      self.cells[offset] = contents

  def init_array(self, col_count, row_count):
    cell_count = col_count * row_count
    cells = [None] * cell_count
    return cells, cell_count

  def get_cell_offset(self, col, row):
    if col < 0 or col >= self.col_count:
      return - 1
    if row < 0 or row >= self.row_count:
      return - 1
    return row * self.col_count + col
  
  def get_cell_colrow(self, offset):
    row = offset / self.col_count
    col = offset - row * self.col_count
    return col, row
  
  def get_cell(self, col, row):
    cell_offset = self.get_cell_offset(col, row)
    if cell_offset < 0:
      return None
    return self.cells[cell_offset]

  def get_cell_cost(self, openset, closedset, offset):
    if offset in openset:
      return openset[offset][1]
    elif offset in closedset:
      return closedset[offset][1]
    else:
      # We were asked to calculate a path from/to an obstacle. 
      return self.col_count + self.row_count + 100
    
  def add_to_openset_if_open(self, openset, closedset,
                             current_offset, col, row):
    candidate_offset = self.get_cell_offset(col, row)
    if candidate_offset < 0:
      return

    if self.cells[candidate_offset]:
      return

    if candidate_offset in closedset:
      return
    if candidate_offset in openset:
      # A candidate is already on the open list. See whether the G score
      # through us is better than its current G score, and if so, change its
      # parent to us and continue
      current_g = self.get_cell_cost(openset, closedset, current_offset) + 1
      candidate_g = self.get_cell_cost(openset, closedset, candidate_offset)
      if current_g < candidate_g:
        openset[candidate_offset] = (current_offset, current_g)
      return
    if candidate_offset == current_offset:
      # Catching this case here lets the main loop look a little more
      # elegant; it can start with an empty openset
      openset[candidate_offset] = (None, 0)
    else:
      current_cost = self.get_cell_cost(openset, closedset, current_offset)
      openset[candidate_offset] = (current_offset, current_cost + 1)

  def move_to_closedset(self, openset, closedset, offset):
    closedset[offset] = openset[offset]
    del openset[offset]

  def find_path(self, start_cell, end_cell):
    start_col = start_cell[0]
    start_row = start_cell[1]
    end_col = end_cell[0]
    end_row = end_cell[1]
    openset = {}
    closedset = {}

    current_col = start_col
    current_row = start_row
    while current_col != end_col or current_row != end_row:
      current_offset = self.get_cell_offset(current_col, current_row)
      self.add_to_openset_if_open(openset, closedset, current_offset,
                                  current_col, current_row)
      self.add_to_openset_if_open(openset, closedset, current_offset,
                                  current_col - 1, current_row)
      self.add_to_openset_if_open(openset, closedset, current_offset,
                                  current_col + 1, current_row)
      self.add_to_openset_if_open(openset, closedset, current_offset,
                                  current_col, current_row - 1)
      self.add_to_openset_if_open(openset, closedset, current_offset,
                                  current_col, current_row + 1)
      if current_offset in openset:
        self.move_to_closedset(openset, closedset, current_offset)
      lowest_cost = 1 + self.col_count + self.row_count
      lowest_offset = None
      for candidate_offset in openset.keys():
        candidate_col, candidate_row = self.get_cell_colrow(candidate_offset)
        # Manhattan distance  
        f = abs(end_col - candidate_col) + abs(end_row - candidate_row)
        if f < lowest_cost:
          lowest_cost = f
          lowest_offset = candidate_offset
      if lowest_offset is None:
        return None
      self.move_to_closedset(openset, closedset, lowest_offset)
      current_col, current_row = self.get_cell_colrow(lowest_offset)

    path = []
    while current_col != start_col or current_row != start_row:
      current_offset = self.get_cell_offset(current_col, current_row)
      path.append((current_col, current_row))
      new_offset = closedset[current_offset][0]
      current_col, current_row = self.get_cell_colrow(new_offset)
    path.append((current_col, current_row))
    path.reverse()
    return path

class Game(object):

  EASY, HARD = (0, 1) 
  LEVELS = [
            (1.0, [ EASY, EASY, EASY ]),
            (1.0, [ EASY, EASY, EASY, HARD ]),
            (1.0, [ EASY, EASY, HARD, EASY, HARD ]),
            (1.2, [ HARD, EASY, HARD, EASY, HARD ]),
            (1.5, [ HARD, HARD, HARD ]),
            (2.0, [ HARD, HARD, HARD, HARD, HARD, HARD ]),
            (2.5, [ HARD, HARD, HARD, HARD, HARD, HARD ]),
            (2.6, [ HARD, HARD, HARD, HARD, HARD, HARD ]),
            (2.7, [ HARD, HARD, HARD, HARD, HARD, HARD ]),
            (2.8, [ HARD, HARD, HARD, HARD, HARD, HARD ]),
            ]

  def __init__(self):
    self.__clock = pygame.time.Clock()
    self.__application_name = 'Tower Defense'

    pygame.init()
    app_icon = pygame.image.load(os.path.join(ASSET_DIR, 'application.png'))
    app_icon_rect = app_icon.get_rect()
    pygame.display.set_icon(app_icon)
    self.__screen = pygame.display.set_mode((SCREEN_SIZE_X, SCREEN_SIZE_Y))
    pygame.display.set_caption(self.__application_name)
    pygame.mouse.set_visible(True)
    
    self.__small_font = get_font(14)
    self.__big_font = get_font(36)
    
    self.generate_game_over_image()
    self.__banner_image = None
    self.__banner_countdown = 0
    self.__banner_alpha = 0
    self.__enqueued_banner_messages = []

    self.__funds = 10
    self.__lives = 10
    self.__game_over = False

    TILE_SIZE = 16
    GRAPH_COL = SCREEN_SIZE_X / TILE_SIZE
    GRAPH_ROW = SCREEN_SIZE_Y / TILE_SIZE
    self.__grid = Grid(GRAPH_COL, GRAPH_ROW, TILE_SIZE)
    self.__entry_grid_pos = (1, GRAPH_ROW / 2)
    self.__exit_grid_pos = (GRAPH_COL - 2, GRAPH_ROW / 2)

    self.__environment_sprites = pygame.sprite.Group()
    for row in range(0, GRAPH_ROW):
      if row == 0 or row == GRAPH_ROW - 1:
        step = 1
      else:
        step = GRAPH_COL - 1
      for col in range(0, GRAPH_COL, step):
        wall = Wall(self.__grid.grid_to_screen((col, row)), self)
        self.__grid.set_cell(col, row, wall)
        self.__environment_sprites.add(wall)

    self.__bases = [Base(self.__grid.grid_to_screen(self.__entry_grid_pos),
                         self),
                    Base(self.__grid.grid_to_screen(self.__exit_grid_pos),
                         self, is_exit=True)]
    self.__environment_sprites.add(self.__bases)
    for base in self.__bases:
      self.__grid.set_cell(base.position[0], base.position[1], base)    

    self.regenerate_path()

    self.__enemy_sprites = pygame.sprite.Group([])
    self.__enemy_sprites.needs_draw_call = True

    self.__background = pygame.Surface(self.__screen.get_size()).convert()
    self.__background.fill(FIELD_BACKGROUND_COLOR)

    self.__sprite_groups = [self.__environment_sprites,
                            self.__enemy_sprites]
    
    self.__sound_victory = load_sound('victory.wav')

    self.__cursor_grid_pos = None
    
    self.__level = 0
    pygame.time.set_timer(BEGIN_LEVEL, 5000)

  def getGrid(self):
      return self.__grid

  def setGrid(self, value):
      self.__grid = value

  def delGrid(self):
      del self.__grid

  def begin_level(self):
    self.enqueue_banner_message('Starting Level %d' % (self.__level + 1))
    self.level_multiplier = Game.LEVELS[self.__level][0]
    self.level_enemy_lineup = Game.LEVELS[self.__level][1]
    self.level_enemy_lineup_index = 0
    self.enemy_lineup_complete = False
    pygame.time.set_timer(SPAWN_ENEMY, 2000)

  def end_level(self):
    self.__level += 1
    if self.__level >= len(Game.LEVELS):
      self.__sound_victory.play()
      self.__game_over = True
      self.enqueue_banner_message('You Win!')
    else:
      pygame.time.set_timer(BEGIN_LEVEL, 3000)
    
  def getFunds(self):
      return self.__funds

  def setFunds(self, value):
      self.__funds = value

  def delFunds(self):
      del self.__funds

  def getExit_grid_pos(self):
      return self.__exit_grid_pos

  def setExit_grid_pos(self, value):
      self.__exit_grid_pos = value

  def delExit_grid_pos(self):
      del self.__exit_grid_pos

  def getPath_map(self):
      return self.__path_map

  def setPath_map(self, value):
      self.__path_map = value

  def delPath_map(self):
      del self.__path_map

  def regenerate_path(self):
    path = self.__grid.find_path(self.__entry_grid_pos, self.__exit_grid_pos)
    if not path:
      print 'ERROR! We ended up with a dead end.'
    else:
      self.__path_map = PathMap(path) 

  def getEnvironment_sprites(self):
      return self.__environment_sprites

  def getBases(self):
      return self.__bases

  def getEnemy_sprites(self):
      return self.__enemy_sprites

  def setEnvironment_sprites(self, value):
      self.__environment_sprites = value

  def setBases(self, value):
      self.__bases = value

  def setEnemy_sprites(self, value):
      self.__enemy_sprites = value

  def delEnvironment_sprites(self):
      del self.__environment_sprites

  def delBases(self):
      del self.__bases

  def delEnemy_sprites(self):
      del self.__enemy_sprites

  def award_kill(self, value):
    self.__funds += value

  def notify_enemy_sprite_change(self):
    if (len(self.__enemy_sprites.sprites()) == 0 and
        self.enemy_lineup_complete):
      print 'level %d complete' % self.__level
      self.end_level()

  def deduct_life(self):
    self.__lives -= 1
    if self.__lives <= 0:
      self.__game_over = True

  def get_next_enemy_type(self):
    if self.level_enemy_lineup_index < len(self.level_enemy_lineup):
      next_enemy = self.level_enemy_lineup[self.level_enemy_lineup_index]
      self.level_enemy_lineup_index += 1
      return next_enemy
    self.enemy_lineup_complete = True
    return None

  def get_enemy_spawn_rate(self):
    return 500

  def spawn(self):
    pos = self.__grid.grid_to_screen(self.__entry_grid_pos)
    enemy_type = self.get_next_enemy_type()
    if enemy_type is None:
      return
    pygame.time.set_timer(SPAWN_ENEMY, self.get_enemy_spawn_rate())
    if enemy_type == Game.EASY:
      attacker = EasyAttacker(pos, self)
    elif enemy_type == Game.HARD:
      attacker = HardAttacker(pos, self)
    else:
      print 'NO ENEMY SPAWNED!'
    self.__enemy_sprites.add(attacker)

  def add_turret(self, grid_position):
    col, row = grid_position[0], grid_position[1]
    if random.randint(0, 2) == 0:
      turret = SmallTurret(self.__grid.grid_to_screen((col, row)), self)
    else:
      turret = BigTurret(self.__grid.grid_to_screen((col, row)), self)
    if self.funds >= turret.COST:
      self.funds -= turret.COST
      self.__grid.set_cell(col, row, turret)
      self.environment_sprites.add(turret)
      self.regenerate_path()

  def remove_turret(self, pos):
    col, row = pos[0], pos[1]
    contents = self.__grid.get_cell(col, row)
    if isinstance(contents, Turret):
      contents.parent_group.remove(contents)
      self.__grid.set_cell(col, row, None)
      self.regenerate_path()
      self.funds += contents.value

  def is_ok_to_place(self, pos):
    col, row = self.__grid.screen_to_grid(pos)
    contents = self.__grid.get_cell(col, row)
    if contents:
      return False
    try:
      self.__grid.set_cell(col, row, 0xdeadbeef)
      if self.__grid.find_path(self.__entry_grid_pos,
                               self.__exit_grid_pos) is not None:
        return True
      else:
        return False
    finally:
      self.__grid.set_cell(col, row, None)

  def handle_mouseup(self, pos):
    col, row = self.__grid.screen_to_grid(pos)
    contents = self.__grid.get_cell(col, row)
    if not contents:
      self.add_turret((col, row))
      return
    if isinstance(contents, Wall):
      return
    if isinstance(contents, Turret):
      self.remove_turret((col, row))
      return
    print 'huh?'

  def handle_mousemotion(self, pos):
    self.__cursor_grid_pos = None
    col, row = self.__grid.screen_to_grid(pos)
    contents = self.__grid.get_cell(col, row)
    if not contents:
      self.__cursor_grid_pos = (col, row)
      self.ok_to_place = self.is_ok_to_place(pos)

  def handle_events(self):
    for event in pygame.event.get():
      if event.type == QUIT:
        return True
      elif event.type == KEYDOWN and event.key == K_ESCAPE:
        return True
      elif event.type == MOUSEBUTTONUP:
        self.handle_mouseup(event.pos)
      elif event.type == MOUSEMOTION:
        self.handle_mousemotion(event.pos)
      elif event.type == SPAWN_ENEMY:
        pygame.time.set_timer(SPAWN_ENEMY, 0)
        self.spawn()
      elif event.type == BEGIN_LEVEL:
        pygame.time.set_timer(BEGIN_LEVEL, 0)
        self.begin_level()
    return False

  def kill_actor_sprite(self, sprite):
    self.__enemy_sprites.remove(sprite)

  def get_level_multiplier(self):
    return 1.0

  def draw_dashboard(self):
    line_height = self.__small_font.get_height()
    position = (5, SCREEN_SIZE_Y - 40)
    cursor = position

    fillrect = pygame.Rect(position, (80, line_height * 2))
    self.__screen.fill(DASH_BACKGROUND_COLOR, fillrect)

    str = '$%d, Lives %d' % (self.__funds, self.__lives)
    text = self.__small_font.render(str, 1, DASH_COLOR)
    textpos = text.get_rect()
    textpos.topleft = cursor
    text.set_alpha(128)
    self.__screen.blit(text, textpos)
    cursor = (cursor[0], cursor[1] + line_height)

    str = 'Level %d' % (self.__level + 1)
    text = self.__small_font.render(str, 1, DASH_COLOR)
    textpos = text.get_rect()
    textpos.topleft = cursor
    text.set_alpha(128)
    self.__screen.blit(text, textpos)
    cursor = (cursor[0], cursor[1] + line_height)

  def generate_game_over_image(self):
    self.game_over_image = pygame.Surface((SCREEN_SIZE_X,
                                           self.__big_font.get_height() + 16))
    self.game_over_image.fill((0, 0, 192))
    self.game_over_image.set_alpha(192)
    text = self.__big_font.render('Game Over', 1, (192, 0, 0))
    textpos = text.get_rect(centerx=self.game_over_image.get_width() / 2)
    textpos.top = 8
    self.game_over_image.blit(text, textpos)

  def draw_game_over(self):
    self.__screen.blit(self.game_over_image,
                       (0, (SCREEN_SIZE_Y -
                            self.game_over_image.get_height()) / 4))

  def enqueue_banner_message(self, text):
    self.__enqueued_banner_messages.append(text)

  def tick_banner(self, msec_since_last):
    if not self.__banner_image:
      try:
        message = self.__enqueued_banner_messages.pop(0)
        if message:
          self.generate_banner(message)
          self.__banner_countdown = 4000
      except IndexError:
        pass
      return
    self.__banner_countdown -= msec_since_last
    if self.__banner_countdown <= 0:
      self.__banner_image = None
    else:
      self.__banner_alpha = float(BANNER_ALPHA)
      if self.__banner_countdown > BANNER_FADE_IN_END:
        self.__banner_alpha *= (float(BANNER_DURATION - self.__banner_countdown) /
                                float(BANNER_DURATION - BANNER_FADE_IN_END))
      elif self.__banner_countdown < BANNER_FADE_OUT_START:
        self.__banner_alpha *= (float(self.__banner_countdown) /
                                BANNER_FADE_OUT_START)
      self.__banner_alpha = int(self.__banner_alpha)
      self.__banner_image.set_alpha(self.__banner_alpha)

  def generate_banner(self, message):
    self.__banner_image = pygame.Surface((SCREEN_SIZE_X,
                                          self.__big_font.get_height() + 16))
    self.__banner_image.fill((0, 0, 192))
    self.__banner_image.set_alpha(self.__banner_alpha)
    text = self.__big_font.render(message, 1, (255, 255, 0))
    textpos = text.get_rect(centerx=self.__banner_image.get_width() / 2)
    textpos.top = 8
    self.__banner_image.blit(text, textpos)

  def draw_banner(self):
    if self.__banner_image:
      self.__screen.blit(self.__banner_image,
                         (0, (SCREEN_SIZE_Y -
                              self.__banner_image.get_height()) / 4))
    
  def run(self):
    while True:
      elapsed = self.__clock.tick(FPS)
      self.tick_banner(elapsed)

      if self.handle_events():
        return

      self.__screen.blit(self.__background, (0, 0))

      if self.__cursor_grid_pos:
        cursor_rect = pygame.Rect(0, 0, 16, 16)
        cursor_rect.center = self.__grid.grid_to_screen(self.__cursor_grid_pos)
        if self.ok_to_place:
          self.__screen.fill((0, 255, 0), cursor_rect)
        else:
          self.__screen.fill((255, 0, 0), cursor_rect)
      for group in self.__sprite_groups:
        if not self.__game_over:
          group.update(elapsed)
        group.draw(self.__screen)
        if hasattr(group, 'needs_draw_call'):
          for sprite in group:
            sprite.draw(self.__screen)
      self.draw_dashboard()
      if self.__game_over:
        self.draw_game_over()
      else:
        self.draw_banner()
      pygame.display.flip()

  environment_sprites = property(getEnvironment_sprites,
                                 setEnvironment_sprites,
                                 delEnvironment_sprites,
                                 "Environment_sprites's Docstring")

  bases = property(getBases, setBases, delBases, "Bases's Docstring")

  enemy_sprites = property(getEnemy_sprites,
                           setEnemy_sprites,
                           delEnemy_sprites,
                           "Enemy_sprites's Docstring")

  path_map = property(getPath_map, setPath_map, delPath_map,
                      "Path_map's Docstring")

  exit_grid_pos = property(getExit_grid_pos,
                           setExit_grid_pos,
                           delExit_grid_pos,
                           "Exit_grid_pos's Docstring")

  funds = property(getFunds, setFunds, delFunds, "Funds's Docstring")

  grid = property(getGrid, setGrid, delGrid, "Grid's Docstring")

def main():
  game = Game()
  game.run()

if __name__ == '__main__':
  main()
