# Copyright (c) 2009 Mike Tsao

# TODO
#
# - carcasses
# - accurate turret shots
# - restart game when over
# - add more enemies and turrets
# - balance the gameplay

from pygame.locals import *
from vec2d import Vec2d
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
    self._layer = 8
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.game = game
    self.is_exit = is_exit
    self.image = pygame.image.load(os.path.join(ASSET_DIR, 'base.png'))
    self.position = position
    self.rect = self.image.get_rect(center=position)

  def update(self, dt):
    pass

class Wall(pygame.sprite.Sprite):
  def __init__(self, position):
    self._layer = 2
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.image = pygame.image.load(os.path.join(ASSET_DIR, 'wall.png'))
    self.position = position
    self.rect = self.image.get_rect(center=position)

  def update(self, dt):
    pass

class Dashboard(pygame.sprite.Sprite):
  BACKGROUND_COLOR = (64, 64, 64)
  COLOR = (255, 255, 0)
  
  def __init__(self, position, game, font, line_count):
    self._layer = 10
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.game = game
    self.font = font
    self.line_count = line_count
    self.line_height = self.font.get_height()
    self.image = pygame.Surface((80, self.line_height * 
                                 self.line_count)).convert()
    self.rect = self.image.get_rect()
    self.rect.left = position[0]
    self.rect.bottom = position[1]

  def update(self, dt):
    cursor = (4, 0)

    self.image.fill(Dashboard.BACKGROUND_COLOR)

    str = '$%d, Lives %d' % (self.game.funds, self.game.lives)
    text = self.font.render(str, 1, Dashboard.COLOR)
    textpos = text.get_rect()
    textpos.topleft = cursor
    text.set_alpha(128)
    self.image.blit(text, textpos)
    cursor = (cursor[0], cursor[1] + self.line_height)

    str = 'Level %d' % (self.game.level + 1)
    text = self.font.render(str, 1, Dashboard.COLOR)
    textpos = text.get_rect()
    textpos.topleft = cursor
    text.set_alpha(128)
    self.image.blit(text, textpos)
    cursor = (cursor[0], cursor[1] + self.line_height)

class TurretMenu(pygame.sprite.Sprite):
  FONT_COLOR = (255, 255, 0)
  WIDTH = 4 * 16 + (4 - 1) * 2 + 8
  
  game = None 

  def __init__(self, position, font):
    self.__selected_turret = None
    self._layer = 10
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.font = font
    self.line_height = self.font.get_height()
    self.image = pygame.Surface((TurretMenu.WIDTH,
                                 16 + self.line_height)).convert()
    self.rect = self.image.get_rect()
    self.rect.right = position[0]
    self.rect.bottom = position[1]

    self.image.fill((64, 64, 64), self.image.get_rect())
    x_cursor = 4

    turret_image = SmallTurret.get_image()
    turret_rect = turret_image.get_rect(left=x_cursor)
    self.image.blit(turret_image, turret_rect)
    x_cursor += 16 + 2

    turret_image = BigTurret.get_image()
    turret_rect = turret_image.get_rect(left=x_cursor)
    self.image.blit(turret_image, turret_rect)
    x_cursor += 16 + 2

    x_cursor = 4 + 8

    str = '%d' % (SmallTurret.COST)
    text = self.font.render(str, 1, TurretMenu.FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = x_cursor
    textpos.top = 16
    self.image.blit(text, textpos)
    x_cursor += 16 + 2

    str = '%d' % (BigTurret.COST)
    text = self.font.render(str, 1, TurretMenu.FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = x_cursor
    textpos.top = 16
    self.image.blit(text, textpos)
    x_cursor += 16 + 2

    self.image_no_selection = self.image
    self.image_selections = []
    for i in range(0, 4):
      image_rect = self.image_no_selection.get_rect()
      image = pygame.Surface(image_rect.size).convert()
      image.blit(self.image_no_selection, image_rect)
      rect = pygame.Rect((4 + i * 16, 0), (16, 16))
      pygame.draw.rect(image, (255, 255, 0), rect, 2)
      self.image_selections.append(image)

  def getSelected_turret(self):
    return self.__selected_turret

  def setSelected_turret(self, value):
    if value is not None and self.__selected_turret == value:
      self.__selected_turret = None
    else:
      self.__selected_turret = value
    self.check_sufficient_funds()

  def delSelected_turret(self):
    del self.__selected_turret

  def check_sufficient_funds(self):
    if self.__selected_turret is not None:
      funds = self.game.funds
      if funds < self.__selected_turret.COST:
        self.__selected_turret = None

  def update(self, dt):
    self.check_sufficient_funds()
    self.image = self.image_no_selection
    if self.__selected_turret is not None:
      if self.__selected_turret == SmallTurret:
        self.image = self.image_selections[0]
      elif self.__selected_turret == BigTurret:
        self.image = self.image_selections[1]

  selected_turret = property(getSelected_turret, setSelected_turret,
                             delSelected_turret, "Selected_turret's Docstring")

class Button(pygame.sprite.Sprite):
  def __init__(self, font, label, action, **kwargs):
    self._layer = 9
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.font = font
    self.action = action
    self.line_height = self.font.get_height()
    text = self.font.render(label, 1, (255, 255, 0))
    textpos = text.get_rect()
    self.image = pygame.Surface(textpos.size).convert()
    self.image.fill((0, 0, 255))
    self.image.blit(text, textpos)
    self.image.set_alpha(192)

    if kwargs.has_key('center'):
      self.rect = self.image.get_rect(center=kwargs['center'])
    if kwargs.has_key('topleft'):
      self.rect = self.image.get_rect(center=kwargs['topleft'])
    if kwargs.has_key('bottomright'):
      self.rect = self.image.get_rect(center=kwargs['bottomright'])

  def update(self, dt):
    pass
  
  def clicked(self):
    self.action()
    self.kill()

class TurretSellMenu(pygame.sprite.Sprite):
  FONT_COLOR = (255, 255, 0)
  WIDTH = 4 * 16 + (4 - 1) * 2 + 8
  
  game = None 

  def __init__(self, position, font):
    self.__selected_turret = None
    self._layer = 10
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.font = font
    self.line_height = self.font.get_height()
    self.image = pygame.Surface((TurretMenu.WIDTH,
                                 16 + self.line_height)).convert()
    self.rect = self.image.get_rect()
    self.rect.right = position[0]
    self.rect.bottom = position[1]

    self.image.fill((64, 64, 64), self.image.get_rect())
    x_cursor = 4

    turret_image = SmallTurret.get_image()
    turret_rect = turret_image.get_rect(left=x_cursor)
    self.image.blit(turret_image, turret_rect)
    x_cursor += 16 + 2

    turret_image = BigTurret.get_image()
    turret_rect = turret_image.get_rect(left=x_cursor)
    self.image.blit(turret_image, turret_rect)
    x_cursor += 16 + 2

    x_cursor = 4 + 8

    str = '%d' % (SmallTurret.COST)
    text = self.font.render(str, 1, TurretMenu.FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = x_cursor
    textpos.top = 16
    self.image.blit(text, textpos)
    x_cursor += 16 + 2

    str = '%d' % (BigTurret.COST)
    text = self.font.render(str, 1, TurretMenu.FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = x_cursor
    textpos.top = 16
    self.image.blit(text, textpos)
    x_cursor += 16 + 2

    self.image_no_selection = self.image
    self.image_selections = []
    for i in range(0, 4):
      image_rect = self.image_no_selection.get_rect()
      image = pygame.Surface(image_rect.size).convert()
      image.blit(self.image_no_selection, image_rect)
      rect = pygame.Rect((4 + i * 16, 0), (16, 16))
      pygame.draw.rect(image, (255, 255, 0), rect, 2)
      self.image_selections.append(image)

  def getSelected_turret(self):
    return self.__selected_turret

  def setSelected_turret(self, value):
    if value is not None and self.__selected_turret == value:
      self.__selected_turret = None
    else:
      self.__selected_turret = value
    self.check_sufficient_funds()

  def delSelected_turret(self):
    del self.__selected_turret

  def check_sufficient_funds(self):
    if self.__selected_turret is not None:
      funds = self.game.funds
      if funds < self.__selected_turret.COST:
        self.__selected_turret = None

  def update(self, dt):
    self.check_sufficient_funds()
    self.image = self.image_no_selection
    if self.__selected_turret is not None:
      if self.__selected_turret == SmallTurret:
        self.image = self.image_selections[0]
      elif self.__selected_turret == BigTurret:
        self.image = self.image_selections[1]

  selected_turret = property(getSelected_turret, setSelected_turret,
                             delSelected_turret, "Selected_turret's Docstring")

class Cursor(pygame.sprite.Sprite):
  def __init__(self):
    self._layer = 4
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.image = pygame.Surface((16, 16)).convert()
    self.rect = self.image.get_rect()
    self.__is_valid_placement = False
    self.__is_buy = False
    self.current_color = None

  def getIs_valid_placement(self):
      return self.__is_valid_placement

  def getIs_buy(self):
      return self.__is_buy

  def setIs_valid_placement(self, value):
      self.__is_valid_placement = value

  def setIs_buy(self, value):
      self.__is_buy = value

  def delIs_valid_placement(self):
      del self.__is_valid_placement

  def delIs_buy(self):
      del self.__is_buy

  def set_position(self, position):
    self.rect.center = position

  def update(self, dt):
    new_color = None
    if self.__is_buy:
      if self.__is_valid_placement:
        new_color = (0, 255, 0)
      else:
        new_color = (255, 0, 0)
    else:
      new_color = (255, 255, 0)
    if new_color != self.current_color:
      self.image.fill(new_color)
      self.current_color = new_color

  is_valid_placement = property(getIs_valid_placement, setIs_valid_placement,
                                delIs_valid_placement,
                                "Is_valid_placement's Docstring")

  is_buy = property(getIs_buy, setIs_buy, delIs_buy, "Is_buy's Docstring")

class GameOver(pygame.sprite.Sprite):
  BACKGROUND_COLOR = (128, 128, 128)
  COLOR = (192, 192, 0)

  def __init__(self, font):
    self._layer = 10
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.font = font
    self.line_height = self.font.get_height()
    self.image = pygame.Surface((SCREEN_SIZE_X,
                                 self.line_height + 16)).convert()
    self.rect = self.image.get_rect()

    self.image.fill((0, 0, 192))
    self.image.set_alpha(192)
    text = self.font.render('Game Over', 1, (192, 0, 0))
    textpos = text.get_rect(centerx=self.image.get_width() / 2)
    textpos.top = 8
    self.image.blit(text, textpos)
    self.rect.topleft = (0,
                         (SCREEN_SIZE_Y - self.rect.height) / 4)

  def update(self, dt):
    pass

class Banner(pygame.sprite.Sprite):
  enqueued_messages = []
  current_banner = None
  font = None
  
  ALPHA = 192
  DURATION = 4000
  FADE_IN_END = 3750
  FADE_OUT_START = 1000

  def __init__(self, message):
    self._layer = 10
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.line_height = Banner.font.get_height()
    height = self.line_height + 16
    self.image = pygame.Surface((SCREEN_SIZE_X, height))
    self.rect = self.image.get_rect(topleft=(0, (SCREEN_SIZE_Y - height) / 4))
    self.image.fill((0, 0, 192))
    text = Banner.font.render(message, 1, (255, 255, 0))
    textpos = text.get_rect(centerx=self.rect.width / 2)
    textpos.top = 8
    self.image.blit(text, textpos)
    self.countdown = 4000

  def tick(dt):
    if not Banner.current_banner:
      try:
        message = Banner.enqueued_messages.pop(0)
        if message:
          Banner.current_banner = Banner(message)
      except IndexError:
        pass
      return
  tick = staticmethod(tick)

  def update(self, dt):
    self.countdown -= dt
    if self.countdown <= 0:
      self.kill()
      Banner.current_banner = None
    else:
      alpha = float(Banner.ALPHA)
      if self.countdown > Banner.FADE_IN_END:
        alpha *= (float(Banner.DURATION - self.countdown) / 
                  float(Banner.DURATION - Banner.FADE_IN_END))
      elif self.countdown < Banner.FADE_OUT_START:
        alpha *= (float(self.countdown) / Banner.FADE_OUT_START)
      self.image.set_alpha(int(alpha))

  def enqueue_message(message):
    Banner.enqueued_messages.append(message)
  enqueue_message = staticmethod(enqueue_message)

  def reset():
    Banner.enqueued_messages = []
    if Banner.current_banner:
      Banner.current_banner.kill()
      Banner.current_banner = None
  reset = staticmethod(reset)

class Explosion(pygame.sprite.Sprite):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'explosion_1.png')
  
  IMAGE_FRAMES = 10
  image = None
  frames = []

  def __init__(self, position):
    self._layer = 2
    pygame.sprite.Sprite.__init__(self, self.containers)
    if Explosion.image is None:
      Explosion.image = pygame.image.load(Explosion.IMAGE_FILENAME)
      colorkey = Explosion.image.get_at((0, 0))
      # Unfortunate SDL limitation that it can't handle surface-wide and per-
      # pixel alpha at the same time. So we fake it.
      for i in range(0, Explosion.IMAGE_FRAMES):
        image = pygame.Surface(Explosion.image.get_rect().size)
        image.set_colorkey(colorkey, RLEACCEL)
        image.set_alpha(255.0 * float(i) / float(Explosion.IMAGE_FRAMES))
        image.blit(Explosion.image, Explosion.image.get_rect())
        Explosion.frames.append(image)
    self.image = pygame.image.load(os.path.join(ASSET_DIR,
                                                'explosion_1.png'))
    self.position = position
    self.rect = self.image.get_rect(center=position)
    self.lifetime_max = 2000
    self.lifetime_fade_start = 1000.0
    self.lifetime = self.lifetime_max

  def update(self, dt):
    self.lifetime -= dt
    if self.lifetime <= 0:
      self.kill()
    else:
      if self.lifetime < self.lifetime_fade_start:
        self.image = Explosion.frames[int(Explosion.IMAGE_FRAMES * 
                                          float(self.lifetime) / 
                                          self.lifetime_fade_start)]

class Attacker(pygame.sprite.Sprite):
  def __init__(self, position, game, image, sound_explosion,
               health, speed, value):
    self._layer = 5
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.image = image
    self.sound_explosion = sound_explosion
    self.position = position
    self.rect = self.image.get_rect(center=position)
    self.original_image = self.image
    self.game = game
    self.angle_degrees = 0
    self.starting_health = health * game.level_multiplier
    self.health = self.starting_health
    self.speed = speed * game.level_multiplier
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
    self.kill()
    self.game.notify_enemy_sprite_change()

  def inflict_damage(self, points):
    self.health -= points
    if self.health <= 0:
      self.sound_explosion.play()
      Explosion(self.position)
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

  def get_image():
    if EasyAttacker.image is None:
      EasyAttacker.image = pygame.image.load(EasyAttacker.IMAGE_FILENAME)
    return EasyAttacker.image
  get_image = staticmethod(get_image)
  
  def __init__(self, position, game):
    if EasyAttacker.sound_explosion is None:
      EasyAttacker.sound_explosion = load_sound('explosion.wav')
    Attacker.__init__(self, position, game,
                      EasyAttacker.get_image(),
                      EasyAttacker.sound_explosion,
                      EasyAttacker.HEALTH,
                      EasyAttacker.SPEED,
                      EasyAttacker.VALUE)

class HardAttacker(Attacker):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'attacker2.png')
  SPEED = 1.8
  HEALTH = 60.0
  VALUE = 5.0
  
  image = None
  sound_explosion = None
  
  def get_image():
    if HardAttacker.image is None:
      HardAttacker.image = pygame.image.load(HardAttacker.IMAGE_FILENAME)
    return HardAttacker.image
  get_image = staticmethod(get_image)
  
  def __init__(self, position, game):
    if HardAttacker.sound_explosion is None:
      HardAttacker.sound_explosion = load_sound('explosion.wav')
    Attacker.__init__(self, position, game,
                      HardAttacker.get_image(),
                      HardAttacker.sound_explosion,
                      HardAttacker.HEALTH,
                      HardAttacker.SPEED,
                      HardAttacker.VALUE)

class Shot(pygame.sprite.Sprite):
  sound_hit = None
  
  def __init__(self, shooter, target, damage_ability):
    if Shot.sound_hit is None:
      Shot.sound_hit = load_sound('hit.wav')
    self._layer = 6
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.target = target
    self.position = shooter.position
    self.end_position = target.position
    self.damage_ability = damage_ability

    self.image = pygame.Surface((2, 2)).convert()
    self.image.fill((96, 96, 0))
    self.rect = self.image.get_rect(center=self.position)

    self.vector = (Vec2d(self.end_position) - Vec2d(self.position)).normalized()
    
    self.lifetime = 1000

  def update(self, dt):
    self.lifetime -= dt
    self.position += self.vector * (4.0 * float(dt) / float(FPS))
    self.rect.center = self.position
    if self.rect.colliderect(self.target.rect):
      if self.target.alive():
        self.sound_hit.play()
        self.target.inflict_damage(self.damage_ability)
      self.kill()
    else:
      if self.lifetime <= 0:
        self.kill()

class Turret(pygame.sprite.Sprite):
  def __init__(self, position, game, image, sound_shot,
               fire_rate=1000.0,
               fire_ratio=2.0,
               damage_ability=5.0,
               cost=0.0,
               splash=False):
    self._layer = 5
    pygame.sprite.Sprite.__init__(self, self.containers)
    self.game = game
    self.image = image
    self.sound_shot = sound_shot
    self.position = position
    self.rect = self.image.get_rect(center=position)
    self.original_image = self.image

    self.angle_degrees = 0
    self.target_angle_degrees = 0
    self.__locked_enemy = None

    self.fire_countdown = random.randint(50, 500)
    self.fire_rate = fire_rate
    self.fire_ratio = fire_ratio
    self.damage_ability = damage_ability
    self.splash = splash # TODO
    self.value = int(cost * 0.8)

  def die(self):
    self.kill()

  def fire(self, enemy):
    self.sound_shot.play()
    shot = Shot(self, enemy, self.damage_ability)

  def lock_target(self, enemy):
    self.__locked_enemy = enemy
    vector = (Vec2d(self.position) - Vec2d(enemy.position)).normalized()
    self.target_angle_degrees = - vector.get_angle()
    
  def check_enemy_collisions(self, dt):
    if self.fire_countdown > 0 and not self.__locked_enemy:
      self.fire_countdown -= dt
      return

    collision_func = pygame.sprite.collide_circle_ratio(self.fire_ratio)
    nearby_enemies = pygame.sprite.spritecollide(self,
                                                 self.game.enemy_sprites,
                                                 False,
                                                 collision_func)
    if len(nearby_enemies) > 0:
      enemy = nearby_enemies[0]
      self.lock_target(enemy)
      self.fire_countdown = self.fire_rate

  def update(self, dt):
    if self.__locked_enemy:
      angle_delta = self.angle_degrees - self.target_angle_degrees
      if abs(angle_delta) < 10:
        self.fire(self.__locked_enemy)
        self.__locked_enemy = None
      else:
        dr = angle_delta / 1.5
        dr *= (1.05 * float(dt) / float(FPS))
        self.angle_degrees -= dr
    self.check_enemy_collisions(dt)
    rotate = pygame.transform.rotate
    self.image = rotate(self.original_image, self.angle_degrees)

class SmallTurret(Turret):
  IMAGE_FILENAME = os.path.join(ASSET_DIR, 'turret.png')
  FIRE_RATE = 250.0
  FIRE_RATIO = 2.0
  DAMAGE_ABILITY = 5.0
  COST = 3.0
  SPLASH = False
  
  image = None
  sound_shot = None
  
  def get_image():
    if SmallTurret.image is None:
      SmallTurret.image = pygame.image.load(SmallTurret.IMAGE_FILENAME)
    return SmallTurret.image
  get_image = staticmethod(get_image)
  
  def __init__(self, position, game):
    if SmallTurret.sound_shot is None:
      SmallTurret.sound_shot = load_sound('shot.wav')
    Turret.__init__(self, position, game, SmallTurret.get_image(),
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

  def get_image():
    if BigTurret.image is None:
      BigTurret.image = pygame.image.load(BigTurret.IMAGE_FILENAME)
    return BigTurret.image
  get_image = staticmethod(get_image)
  
  
  def __init__(self, position, game):
    if BigTurret.sound_shot is None:
      BigTurret.sound_shot = load_sound('shot.wav')
    Turret.__init__(self, position, game, BigTurret.get_image(),
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

  def is_ok_to_place(self, entry_pos, exit_pos, pos):
    col, row = self.screen_to_grid(pos)
    contents = self.get_cell(col, row)
    if contents:
      return False
    try:
      self.set_cell(col, row, 0xdeadbeef)
      if self.find_path(entry_pos, exit_pos) is not None:
        return True
      else:
        return False
    finally:
      self.set_cell(col, row, None)

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
    pygame.display.set_caption(self.__application_name)
    pygame.mouse.set_visible(True)

    self.__small_font = get_font(14)
    self.__big_font = get_font(36)
    Banner.font = self.__big_font

    self.__background_sprites = pygame.sprite.RenderUpdates()
    self.__widget_sprites = pygame.sprite.RenderUpdates()
    self.__enemy_sprites = pygame.sprite.RenderUpdates()
    self.__foreground_sprites = pygame.sprite.RenderUpdates()
    self.__all_sprites = pygame.sprite.LayeredUpdates()

    Dashboard.containers = self.__foreground_sprites, self.__all_sprites
    Button.containers = self.__widget_sprites, self.__all_sprites
    TurretMenu.containers = self.__foreground_sprites, self.__all_sprites
    Cursor.containers = self.__background_sprites, self.__all_sprites
    Banner.containers = self.__foreground_sprites, self.__all_sprites
    GameOver.containers = self.__foreground_sprites, self.__all_sprites
    Wall.containers = self.__background_sprites, self.__all_sprites
    Explosion.containers = self.__background_sprites, self.__all_sprites
    Shot.containers = self.__background_sprites, self.__all_sprites
    Base.containers = self.__background_sprites, self.__all_sprites
    Turret.containers = self.__background_sprites, self.__all_sprites
    Attacker.containers = self.__enemy_sprites, self.__all_sprites
    
    TurretMenu.game = self

    self.__sound_victory = load_sound('victory.wav')

    self.__cursor = None

    self.__sell_button = None
    self.__upgrade_button = None
    self.__game_over_button = None

    self.start_game()

  def start_game(self):
    for sprite in self.__background_sprites:
      sprite.kill()
    for sprite in self.__widget_sprites:
      sprite.kill()
    for sprite in self.__enemy_sprites:
      sprite.kill()
    self.create_environment()

    self.__level = 0
    self.__funds = 10
    self.__lives = 10
    self.__game_over = False
    pygame.time.set_timer(BEGIN_LEVEL, 5000)
    Banner.reset()

  def create_environment(self):
    TILE_SIZE = 16
    GRAPH_COL = SCREEN_SIZE_X / TILE_SIZE
    GRAPH_ROW = SCREEN_SIZE_Y / TILE_SIZE - 1
    self.__grid = Grid(GRAPH_COL, GRAPH_ROW, TILE_SIZE)
    self.__entry_grid_pos = (1, GRAPH_ROW / 2)
    self.__exit_grid_pos = (GRAPH_COL - 2, GRAPH_ROW / 2)

    for row in range(0, GRAPH_ROW):
      if row == 0 or row == GRAPH_ROW - 1:
        step = 1
      else:
        step = GRAPH_COL - 1
      for col in range(0, GRAPH_COL, step):
        wall = Wall(self.__grid.grid_to_screen((col, row)))
        self.__grid.set_cell(col, row, wall)

    self.regenerate_path()

    self.__bases = [Base(self.__grid.grid_to_screen(self.__entry_grid_pos),
                         self),
                    Base(self.__grid.grid_to_screen(self.__exit_grid_pos),
                         self, is_exit=True)]
    for base in self.__bases:
      self.__grid.set_cell(base.position[0], base.position[1], base)    

  def begin_level(self):
    Banner.enqueue_message('Level %d' % (self.__level + 1))
    self.__level_multiplier = Game.LEVELS[self.__level][0]
    self.__level_enemy_lineup = Game.LEVELS[self.__level][1]
    self.__level_enemy_lineup_index = 0
    self.enemy_lineup_complete = False
    pygame.time.set_timer(SPAWN_ENEMY, 2000)

  def end_level(self):
    self.__level += 1
    if self.__level >= len(Game.LEVELS):
      self.__sound_victory.play()
      self.__game_over = True
      Banner.enqueue_message('You Win!')
    else:
      pygame.time.set_timer(BEGIN_LEVEL, 3000)

  def regenerate_path(self):
    path = self.__grid.find_path(self.__entry_grid_pos, self.__exit_grid_pos)
    if not path:
      print 'ERROR! We ended up with a dead end.'
    else:
      self.__path_map = PathMap(path) 

  def award_kill(self, value):
    self.__funds += value

  def notify_enemy_sprite_change(self):
    if (len(self.__enemy_sprites.sprites()) == 0 and
        self.enemy_lineup_complete):
      self.end_level()

  def deduct_life(self):
    self.__lives -= 1
    if self.__lives <= 0:
      self.__game_over = True

  def get_next_enemy_type(self):
    if self.__level_enemy_lineup_index < len(self.__level_enemy_lineup):
      next_enemy = self.__level_enemy_lineup[self.__level_enemy_lineup_index]
      self.__level_enemy_lineup_index += 1
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

  def add_turret(self, grid_position):
    if not self.__turret_menu.selected_turret:
      return
    col, row = grid_position[0], grid_position[1]
    turret = None
    if self.__turret_menu.selected_turret == SmallTurret:
      if self.funds >= SmallTurret.COST:
        turret = SmallTurret(self.__grid.grid_to_screen((col, row)), self)
    else:
      if self.funds >= BigTurret.COST:
        turret = BigTurret(self.__grid.grid_to_screen((col, row)), self)
    if turret is not None:
      self.funds -= turret.COST
      self.__grid.set_cell(col, row, turret)
      self.regenerate_path()

  def remove_turret(self, pos):
    col, row = pos[0], pos[1]
    contents = self.__grid.get_cell(col, row)
    if isinstance(contents, Turret):
      contents.kill()
      self.__grid.set_cell(col, row, None)
      self.regenerate_path()
      self.funds += contents.value

  def upgrade_turret(self, pos):
    col, row = pos[0], pos[1]
    contents = self.__grid.get_cell(col, row)
    if isinstance(contents, Turret):
      print 'upgrade!'

  def reset_turret_buttons(self):
    if self.__sell_button:
      self.__sell_button.kill()
      self.__sell_button = None
    if self.__upgrade_button:
      self.__upgrade_button.kill()
      self.__upgrade_button = None
      
  def generate_turret_buttons(self, turret):
    self.reset_turret_buttons()    
    col, row = self.__grid.screen_to_grid(turret.position)
    c = self.__grid.grid_to_screen((col, row))
    self.__sell_button = Button(self.__small_font, "Sell $%d" % turret.value,
                                lambda: self.remove_turret((col, row)),
                                center=(c[0] - 40, c[1]))
    self.__upgrade_button = Button(self.__small_font, "Upgrade",
                                   lambda: self.upgrade_turret((col, row)),
                                   center=(c[0] + 40, c[1]))

  def handle_turret_button_clicks(self, pos):
    if self.__sell_button and self.__sell_button.rect.collidepoint(pos):
      self.__sell_button.clicked()
      return True
    elif self.__upgrade_button and self.__upgrade_button.rect.collidepoint(pos):
      self.__upgrade_button.clicked()
      return True
    return False

  def reset_game_over_button(self):
    if self.__game_over_button:
      self.__game_over_button.kill()
      self.__game_over_button = None
      
  def handle_game_over_button_click(self, pos):
    if self.__game_over_button and self.__game_over_button.rect.collidepoint(pos):
      self.reset_game_over_button()
      self.start_game()
      return True
    return False

  def handle_mouseup(self, pos):
    generated_turret_buttons = False
    try:
      if self.handle_turret_button_clicks(pos):
        return
      if self.handle_game_over_button_click(pos):
        return
      if self.__turret_menu.rect.collidepoint(pos):
        local_pos = (pos[0] - self.__turret_menu.rect.left,
                     pos[1] - self.__turret_menu.rect.top)
        if local_pos[1] >= 16:
          self.__turret_menu.selected_turret = None
          return
        horizontal = (local_pos[0] - 4) / 16
        if horizontal <= 0:
          self.__turret_menu.selected_turret = SmallTurret
        elif horizontal == 1:
          self.__turret_menu.selected_turret = BigTurret
        else:
          self.__turret_menu.selected_turret = None
        return
      else:
        col, row = self.__grid.screen_to_grid(pos)
        contents = self.__grid.get_cell(col, row)
        if not contents:
          if not self.__turret_menu.selected_turret:
            return
          self.add_turret((col, row))
          return
        if isinstance(contents, Wall):
          return
        if isinstance(contents, Turret):
          generated_turret_buttons = True
          self.generate_turret_buttons(contents)
          return
        print 'huh?'
    finally:
      if not generated_turret_buttons:
        self.reset_turret_buttons()

  def handle_mousemotion(self, pos):
    col, row = self.__grid.screen_to_grid(pos)
    contents = self.__grid.get_cell(col, row)
    if contents:
      if isinstance(contents, Turret):
        if not self.__cursor:
          cursor = Cursor()
          self.__cursor = cursor
        self.__cursor.set_position(self.__grid.grid_to_screen((col, row)))
        self.__cursor.is_buy = False
        return
    else:
      if self.__turret_menu.selected_turret is not None:
        if not self.__cursor:
          cursor = Cursor()
          self.__cursor = cursor
        self.__cursor.set_position(self.__grid.grid_to_screen((col, row)))
        self.__cursor.is_valid_placement = \
        self.__grid.is_ok_to_place(self.__entry_grid_pos,
                                   self.__exit_grid_pos,
                                   pos)
        self.__cursor.is_buy = True
        return
    if self.__cursor:
      self.__cursor.kill()
      self.__cursor = None

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

  def handle_game_over(self):
    if Banner.current_banner:
      Banner.current_banner.kill()
      Banner.current_banner = None
    self.__game_over_button = Button(self.__big_font, "Play Again",
                                     lambda: self.start_game(),
                                     center=(SCREEN_SIZE_X / 2, SCREEN_SIZE_Y / 2))

  def run(self):
    screen = pygame.display.set_mode((SCREEN_SIZE_X, SCREEN_SIZE_Y))
    background = pygame.image.load(os.path.join(ASSET_DIR, 'background.png'))
    screen.blit(background, background.get_rect())
    pygame.display.update()

    dashboard = Dashboard((5, SCREEN_SIZE_Y), self, self.__small_font, 2)
    self.__turret_menu = TurretMenu((SCREEN_SIZE_X - 5,
                                     SCREEN_SIZE_Y), self.__small_font)
    game_over = None

    while True:
      elapsed = self.__clock.tick(FPS)
      if not self.__game_over:
        Banner.tick(elapsed)

      if self.handle_events():
        return

      if not self.__game_over:
        self.__all_sprites.update(elapsed)

      self.__all_sprites.clear(screen, background)
      dirty = self.__all_sprites.draw(screen)
      for sprite in self.__enemy_sprites:
        sprite.draw(screen)

      if self.__game_over:
        if not game_over:
          game_over = GameOver(self.__big_font)
          self.handle_game_over()
      else:
        if game_over:
          game_over.kill()
          game_over = None

      pygame.display.update(dirty)

  def getFunds(self):
      return self.__funds

  def getLives(self):
      return self.__lives

  def getLevel(self):
      return self.__level

  def setFunds(self, value):
      self.__funds = value

  def setLives(self, value):
      self.__lives = value

  def setLevel(self, value):
      self.__level = value

  def delFunds(self):
      del self.__funds

  def delLives(self):
      del self.__lives

  def delLevel(self):
      del self.__level

  def getEnemy_sprites(self):
      return self.__enemy_sprites

  def setEnemy_sprites(self, value):
      self.__enemy_sprites = value

  def delEnemy_sprites(self):
      del self.__enemy_sprites

  def getGrid(self):
      return self.__grid

  def setGrid(self, value):
      self.__grid = value

  def delGrid(self):
      del self.__grid

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

  def getBases(self):
      return self.__bases

  def setBases(self, value):
      self.__bases = value

  def delBases(self):
      del self.__bases

  def getLevel_multiplier(self):
      return self.__level_multiplier

  def setLevel_multiplier(self, value):
      self.__level_multiplier = value

  def delLevel_multiplier(self):
      del self.__level_multiplier

  bases = property(getBases, setBases, delBases, "Bases's Docstring")

  path_map = property(getPath_map, setPath_map, delPath_map,
                      "Path_map's Docstring")

  exit_grid_pos = property(getExit_grid_pos,
                           setExit_grid_pos,
                           delExit_grid_pos,
                           "Exit_grid_pos's Docstring")

  funds = property(getFunds, setFunds, delFunds, "Funds's Docstring")

  grid = property(getGrid, setGrid, delGrid, "Grid's Docstring")

  enemy_sprites = property(getEnemy_sprites, setEnemy_sprites,
                           delEnemy_sprites, "Enemy_sprites's Docstring")

  funds = property(getFunds, setFunds, delFunds, "Funds's Docstring")

  lives = property(getLives, setLives, delLives, "Lives's Docstring")

  level = property(getLevel, setLevel, delLevel, "Level's Docstring")

  level_multiplier = property(getLevel_multiplier, setLevel_multiplier,
                              delLevel_multiplier,
                              "Level_multiplier's Docstring")

def main():
  game = Game()
  game.run()

if __name__ == '__main__':
  main()
