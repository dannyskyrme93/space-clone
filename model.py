from pyglet.window import key
import enum
from random import randint
from abc import ABCMeta, abstractmethod


class GameModel:
    MODEL_WIDTH = 800
    MODEL_HEIGHT = 600

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def get_game_events(self, dt):
        pass

    @abstractmethod
    def action(self):
        pass


class GameEvent:
    class EventType(enum.Enum):
        BLOOD_IMPACT = 1
        PLAYER_DEATH = 2
        EXPLOSION = 3
        GAME_OVER = 4
        EXIT_MENU = 5
        NEXT_LEVEL = 6
        LIFE_LOST = 7
        ALIEN_1_FIRE = 8
        PLAYER_FIRE = 9
        PLAYER_DEATH_SOUND = 10
        RESET_SCREEN = 11
        SCREEN_EDGE = 12
        ALIEN_MOVE = 13
        PLAYER_IMG_CHANGE = 14
        POINT_ADD = 15

    def __init__(self, type_of, coordinates=None, sound=None, args=None):
        self.type = type_of
        self.coordinates = coordinates
        self.sound = sound
        self.args = args

    def __repr__(self):
        return f'{self.type}, at: {self.coordinates}\nwith sound: {self.sound} and args: {self.args}.'


'''
class RandomEvents:
    class EventType:
        ALIEN_SHOOT = 1
        PLAYER_FIRE_BONUS = 2
        STRAY_ALIEN = 3

    def __init__(self, type_of, coordinates=None, sound=None, args=None):
        self.type = type_of
        self.coordinates = coordinates
        self.sound = sound
        self.args = args
'''


class GameObject:
    def __init__(self, x, y, width, height, img_name):
        self.x = x  # x-coordinate from 0 to MODEL_WIDTH
        self.y = y  # y-coordinate from 0 to MODEL_HEIGHT
        self.img_name = img_name  # file name without folder dir (img) but with the extension (.png, .jpg etc)
        self.width = width
        self.height = height
        self.dx = 0
        self.dy = 0
        self.is_active = True
        self.is_blown = False
        self.is_double_blown = False


change_dict = {'points': 0, 'lives': 3, 'tick_speed': 60, 'alien_shoot_rate': 56}


class Model(GameModel):
    PLAYER_SPEED = GameModel.MODEL_WIDTH / 200
    ALIEN_WIDTH = GameModel.MODEL_WIDTH / 25
    ALIEN_HEIGHT = GameModel.MODEL_HEIGHT / 15
    ALIEN_Y_OFF = GameModel.MODEL_HEIGHT / 30  # Offset from top of screen.
    ALIEN_X_OFF = GameModel.MODEL_WIDTH / 40  # Offset from side of screen.
    PLAYER_LIVES = 2

    def __init__(self):
        super().__init__()
        self.points = 0
        self.game_over = False
        self.tick = 1
        self.tick_speed = 60
        self.time = None
        self.ALIEN_MOVE_RIGHT = True
        self.bullets = []
        self.alien_bullets = []
        self.bullet_max = 4
        self.alien_bullet_max = 100
        self.bullet_height = Model.MODEL_HEIGHT / 19
        self.bullet_dy = Model.MODEL_HEIGHT / 100
        self.countdown = 20
        self.input = True
        self.q_countdown = self.countdown
        self.e_countdown = self.countdown
        self.keys_pressed = 0
        self.events = []
        self.objects = []  # list of Game Objects, will automatically draw on screen
        self.player = GameObject(self.MODEL_WIDTH / 2, self.MODEL_WIDTH / 20,
                                 self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "x-wing.png")
        self.player_lives = 3
        print(self.player.__dict__)

        alien_number = 0
        alien_rows = 0
        alien_columns = 0
        alien_y = self.MODEL_HEIGHT - self.ALIEN_Y_OFF - self.ALIEN_HEIGHT  # Alien spawn y starting point.
        while alien_y > self.MODEL_HEIGHT / 2 and alien_rows < 4:  # Alien y spawn endpoint.
            alien_x = Model.ALIEN_X_OFF * 3  # Alien spawn x starting point.
            while alien_x < self.MODEL_WIDTH - self.ALIEN_X_OFF * 4 and alien_columns < 15:  # Alien x spawn endpoint.
                self.objects += [Alien(alien_x, alien_y, self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "alien.png")]
                alien_number += 1

                if alien_columns == 0 and alien_rows == 0:
                    self.BOX_START = self.objects[-1].x

                alien_x += self.ALIEN_WIDTH * 1.5  # Next alien spawn in row.
                alien_columns += 1

                if alien_columns == 14 and alien_rows == 0:
                    self.BOX_END = self.objects[-1].x + Model.ALIEN_WIDTH  # Dynamic Box end spawn

            alien_y -= self.ALIEN_HEIGHT * 1.3  # Next alien spawn in column.
            alien_rows += 1
            alien_columns = 0

        self.aliens = alien_number

    @property
    def player_center(self):
        return self.player.x + self.player.width / 2, self.player.y + self.player.height / 2

    def get_game_events(self):
        return self.events

    def random_events(self, mob):
        if randint(0, 56) == 56 and len(self.alien_bullets) < self.alien_bullet_max and mob.y >= Model.MODEL_HEIGHT / 3:
            self.alien_bullets.append([mob.x + mob.width / 2, mob.y + mob.height / 2])
            self.events.append(GameEvent(GameEvent.EventType.ALIEN_1_FIRE, sound="bomb1.mp3"))

    def alien_movement_update(self, x_update, y_update):
        for mob in self.objects[:]:
            self.update_position(mob, x_update, y_update)
            # self.events.append(GameEvent(GameEvent.EventType.ALIEN_MOVE, sound="x.mp3"))  #  Alien move sound
            self.random_events(mob)

    def alien_update(self):
        if self.ALIEN_MOVE_RIGHT:
            self.BOX_START += Model.MODEL_WIDTH / 40
            self.BOX_END += Model.MODEL_WIDTH / 40
            if self.BOX_END >= Model.MODEL_WIDTH - Model.ALIEN_X_OFF:  # Checks if box is off screen also
                # self.events.append(GameEvent(GameEvent.EventType.EDGE_SCREEN, sound="x.mp3"))  # Alien hit screen edge
                self.alien_movement_update(0, -Model.ALIEN_HEIGHT)
                self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                self.alien_movement_update(Model.MODEL_WIDTH / 40, 0)

        elif not self.ALIEN_MOVE_RIGHT:
            self.BOX_START -= Model.MODEL_WIDTH / 40
            self.BOX_END -= Model.MODEL_WIDTH / 40
            if self.BOX_START <= 0 + Model.ALIEN_X_OFF:
                # self.events.append(GameEvent(GameEvent.EventType.EDGE_SCREEN, sound="x.mp3"))  # Alien hit screen edge
                self.alien_movement_update(0, -Model.ALIEN_HEIGHT)
                self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                self.alien_movement_update(-Model.MODEL_WIDTH / 40, 0)

    def hitbox_check(self, hitter, hitee):
        if hitter in self.objects and hitee == self.player:
            point_list = ((hitter.x, hitter.y), (hitter.x + hitter.width, hitter.y),
                          (hitter.x, hitter.y + hitter.height),
                          (hitter.x + hitter.width, hitter.y + hitter.height))
        elif hitter in self.bullets:
            point_list = [(hitter[0], hitter[1] + self.bullet_height)]
        elif hitter in self.alien_bullets:
            point_list = [(hitter[0], hitter[1])]
        else:
            return 0

        for point in point_list:
            if hitee.x <= point[0] <= hitee.x + hitee.width and hitee.y <= point[1] <= hitee.y + hitee.height:
                return True

    def player_edge_check(self):
        if self.player.x <= 0:
            # self.events.append(GameEvent(GameEvent.EventType.SCREEN_EDGE, sound="x.mp3")) player hit screen edge
            if self.player.dx < 0:  # Stops infinite dx = 0 at edges
                self.player.dx = 0
        elif self.player.x + self.player.width >= Model.MODEL_WIDTH:
            # self.events.append(GameEvent(GameEvent.EventType.SCREEN_EDGE, sound="x.mp3")) player hit screen edge
            if self.player.dx > 0:
                self.player.dx = 0

    def player_speed_trunc(self):
        if self.player.dx < -Model.PLAYER_SPEED:
            self.player.dx = -Model.PLAYER_SPEED
            print('speed_trunc!')
        elif self.player.dx > Model.PLAYER_SPEED:
            self.player.dx = Model.PLAYER_SPEED
            print('speed_trunc!')

    def player_death_check(self, bullet=(0, 0)):
            for mob in self.objects[:]:
                if mob.y <= 0:  # Monsters off bottom edge of screen
                    self.player.is_double_blown, self.player.is_blown = True, True
                    self.player.img_name = "x-wing_very_burnt.png"

                elif mob.y <= self.player.y + self.player.height:
                    if self.hitbox_check(mob, self.player):
                        self.player.is_double_blown, self.player.is_blown = True, True
                        self.player.img_name = "x-wing_very_burnt.png"

            if self.hitbox_check(bullet, self.player):
                self.alien_bullets.remove(bullet)
                if self.player.is_blown:  # If player hit once
                    self.player.is_double_blown = True
                    self.player.img_name = "x-wing_very_burnt.png"
                if not self.player.is_blown:  # Player hit nonce
                    self.player.is_blown = True
                    self.player.img_name = "x-wing_burnt.png"

    def alien_death_check(self, bullet):
        for mob in self.objects[:]:
            if self.hitbox_check(bullet, mob):
                self.events.append(GameEvent(GameEvent.EventType.BLOOD_IMPACT,
                                             (bullet[0], bullet[1] + self.bullet_height)))
                self.events.append(GameEvent(GameEvent.EventType.POINT_ADD,
                                             coordinates=[bullet[0], bullet[1] + self.bullet_height], args=100))
                self.points += 100
                self.objects.remove(mob)
                self.aliens -= 1
                self.bullets.remove(bullet)

    def screen_change(self, dt):
        if self.player.is_double_blown:  # Aliens reach bottom of screen or Alien kill player or aliens shoot player
            if self.real_timer(dt, 3):
                if self.tick % 10 == 0:
                    self.key_neutraliser()
                    self.alien_ending()
            else:
                self.player.is_active = False
                Model.PLAYER_LIVES -= 1
                self.events.append(GameEvent(GameEvent.EventType.LIFE_LOST, args=self.player_lives))
                self.events.append(GameEvent(GameEvent.EventType.PLAYER_DEATH, coordinates=self.player_center))

                if Model.PLAYER_LIVES == 0:  # TODO temp while player lives not implemented
                    self.events.append(GameEvent(GameEvent.EventType.GAME_OVER))
                    self.game_over = True
                else:
                    self.events.append(GameEvent(GameEvent.EventType.RESET_SCREEN))

        elif self.player.is_active and self.aliens <= 0:  # Player defeated aliens
            self.events.append(GameEvent(GameEvent.EventType.NEXT_LEVEL))  # reset screen with next level, tick speed faster, more bullets from aliens

    def alien_ending(self, random=0):  # TODO work out why aliens aren't leaving screen smoothly
        for mob in self.objects:
            if random:
                self.random_events(mob)
            if mob.y + mob.height < 0:
                self.objects.remove(mob)
                self.aliens -= 1
            self.update_position(mob, 0, -Model.MODEL_HEIGHT / 20)

    def alien_bullet_update(self):
        for bullet in self.alien_bullets:
            bullet[1] -= self.bullet_dy

            if bullet[1] <= 0:
                self.alien_bullets.remove(bullet)

            if bullet[1] <= self.player.y + self.player.height:
                self.player_death_check(bullet)

    def bullet_update(self):
        for bullet in self.bullets:
            bullet[1] += self.bullet_dy

            if bullet[1] >= Model.MODEL_HEIGHT:
                self.bullets.remove(bullet)

            self.alien_death_check(bullet)

    def update_position(self, piece, dx, dy):
        piece.dx = dx
        piece.dy = dy
        piece.x += dx
        piece.y += dy

    def timekeeper(self):
        if not self.q_countdown <= 0:
            self.q_countdown -= 1
        if not self.e_countdown <= 0:
            self.e_countdown -= 1
        self.tick += 1

    def real_timer(self, dt, time):
        if self.time is None:
            self.time = time

        if self.time <= 0:
            print("Time's up")
            self.time = None
            return False
        else:
            self.time -= dt
            return True

    def update(self, dt):
        self.player_death_check()
        self.screen_change(dt)

        if self.tick % self.tick_speed == 0:
            self.tick = 0
            if not self.player.is_blown:
                self.alien_update()
            elif self.aliens > 0:
                self.events.append(GameEvent(GameEvent.EventType.EXPLOSION, self.player_center))
                self.alien_ending(random=True)

        self.player_speed_trunc()
        self.player_edge_check()
        self.update_position(self.player, self.player.dx, self.player.dy)
        self.bullet_update()
        self.alien_bullet_update()
        self.timekeeper()

    def reset(self):
        pass

    def key_neutraliser(self):
        self.input = False
        if self.keys_pressed > 0:
            self.keys_pressed = 0
            self.player.dx = 0

    def controller_logic(self, input_type):
        if input_type == 'release':
            if self.player.x <= 0 or self.player.x + self.player.width >= Model.MODEL_WIDTH:
                print('a')
                return True
            if self.keys_pressed == 0 and self.player.dx == 0:
                print('b')
                return True

        elif input_type == 'press':
            if self.player.x <= 0 and self.player.dx < 0:
                return True
            if self.player.x + self.player.width >= Model.MODEL_WIDTH and self.player.dx > 0:
                return True

    def action(self, key_val: str, action_type: int):
        import view, frame  # avoids circular imports
        x1_ship = self.player.width / 32
        x2_ship = self.player.width / float(1.04065)
        y_ship = self.player.height / 1.6

        if action_type == view.KEY_PRESS:
            if self.game_over:
                if key_val == key.SPACE:
                    self.events.append(GameEvent(GameEvent.EventType.RESET_SCREEN))

                elif key_val == key.R:
                    self.events.append(GameEvent(GameEvent.EventType.EXIT_MENU))

            if self.input:
                if key_val == key.LEFT or key_val == key.RIGHT:
                    self.keys_pressed += 1
                    if not self.controller_logic('press'):
                        if key_val == key.LEFT:
                            self.player.dx -= Model.PLAYER_SPEED
                        else:
                            self.player.dx += Model.PLAYER_SPEED

                elif key_val == key.Q and self.q_countdown <= 0:
                    print("Wow! The Q has been pressed")
                    if len(self.bullets) < self.bullet_max:
                        self.events.append(GameEvent(GameEvent.EventType.PLAYER_FIRE, sound="laser1.mp3"))
                        self.bullets.append([self.player.x + x1_ship, self.player.y + y_ship])
                        self.q_countdown = self.countdown

                elif key_val == key.W and self.e_countdown <= 0:
                    print("Wow! The E has been pressed")
                    if len(self.bullets) < self.bullet_max:
                        self.events.append(GameEvent(GameEvent.EventType.PLAYER_FIRE, sound="laser1.mp3"))
                        self.bullets.append([self.player.x + x2_ship, self.player.y + y_ship])
                        self.e_countdown = self.countdown

                if frame.GameFrame.dev_mode:
                    if key_val == key.G:
                        self.events.append(GameEvent(GameEvent.EventType.GAME_OVER))
                        self.game_over = True

                    elif key_val == key.T:
                        self.events.append(GameEvent(GameEvent.EventType.EXIT_MENU))

                    elif key_val == key.Y:
                        self.events.append(GameEvent(GameEvent.EventType.NEXT_LEVEL))

        if action_type == view.KEY_RELEASE:
            if self.input:
                if key_val == key.LEFT or key_val == key.RIGHT:
                    self.keys_pressed -= 1
                    if self.keys_pressed < 0:
                        self.keys_pressed = 0
                    if not self.controller_logic('release'):
                        self.player.dx += (1 if self.player.dx < 0 else -1) * Model.PLAYER_SPEED


class Alien(GameObject):
    def __init__(self, x, y, width, height, img_name):
        super().__init__(x, y, width, height, img_name)
        self.dx = 1
