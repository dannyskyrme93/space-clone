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
        RESET_SCREEN = 10

    def __init__(self, type_of, coordinates=None, sound=None, args=None):
        self.type = type_of
        self.coordinates = coordinates
        self.sound = sound
        self.args = args

    def __repr__(self):
        return f'{self.type}, at: {self.coordinates}\nwith sound: {self.sound} and args: {self.args}.'


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


class Model(GameModel):
    PLAYER_SPEED = GameModel.MODEL_WIDTH / 200
    ALIEN_WIDTH = GameModel.MODEL_WIDTH / 25
    ALIEN_HEIGHT = GameModel.MODEL_HEIGHT / 15
    ALIEN_Y_OFF = GameModel.MODEL_HEIGHT / 30  # Offset from top of screen.
    ALIEN_X_OFF = GameModel.MODEL_WIDTH / 40  # Offset from side of screen.

    def __init__(self):
        super().__init__()
        self.game_over = False
        self.timer = 0
        self.tick = 1
        self.tick_speed = 40
        self.ALIEN_MOVE_RIGHT = True
        self.bullets = []
        self.alien_bullets = []
        self.bullet_max = 4
        self.alien_bullet_max = 100
        self.bullet_height = Model.MODEL_HEIGHT / 20
        self.bullet_dy = Model.MODEL_HEIGHT / 100
        self.countdown = 20
        self.q_countdown = self.countdown
        self.e_countdown = self.countdown
        self.keys_pressed = 0
        self.events = []
        self.objects = []  # list of Game Objects, will automatically draw on screen
        self.player = GameObject(self.MODEL_WIDTH / 2, self.MODEL_WIDTH / 20,
                                 self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "x-wing.png")
        self.player_lives = 3
        print(self.player.__dict__)

        alien_rows = 0
        alien_columns = 0
        alien_y = self.MODEL_HEIGHT - self.ALIEN_Y_OFF - self.ALIEN_HEIGHT  # Alien spawn y starting point.
        while alien_y > self.MODEL_HEIGHT / 2 and alien_rows < 4:  # Alien y spawn endpoint.
            alien_x = Model.ALIEN_X_OFF * 3  # Alien spawn x starting point.
            while alien_x < self.MODEL_WIDTH - self.ALIEN_X_OFF * 4 and alien_columns < 15:  # Alien x spawn endpoint.
                self.objects += [Alien(alien_x, alien_y, self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "alien.png")]

                if alien_columns == 0 and alien_rows == 0:
                    self.BOX_START = self.objects[-1].x

                alien_x += self.ALIEN_WIDTH * 1.5  # Next alien spawn in row.
                alien_columns += 1

                if alien_columns == 14 and alien_rows == 0:
                    self.BOX_END = self.objects[-1].x + Model.ALIEN_WIDTH  # Dynamic Box end spawn

            alien_y -= self.ALIEN_HEIGHT * 1.3  # Next alien spawn in column.
            alien_rows += 1
            alien_columns = 0

    def get_game_events(self):
        return self.events

    def random_events(self):
        pass

    def alien_movement_update(self, x_update, y_update):
        for obj in self.objects[:]:
            self.update_position(obj, x_update, y_update)
            if randint(0, 44) >= 44 and len(self.alien_bullets) < self.alien_bullet_max and obj.y >= Model.MODEL_HEIGHT / 3:
                self.alien_bullets.append([obj.x + obj.width / 2, obj.y + obj.height / 2])

    def alien_update(self):
        if self.ALIEN_MOVE_RIGHT:
            self.BOX_START += Model.MODEL_WIDTH / 40
            self.BOX_END += Model.MODEL_WIDTH / 40
            if self.BOX_END >= Model.MODEL_WIDTH - Model.ALIEN_X_OFF:  # Checks if box is off screen also
                self.alien_movement_update(0, -Model.ALIEN_HEIGHT)
                self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                self.alien_movement_update(Model.MODEL_WIDTH / 40, 0)

        elif not self.ALIEN_MOVE_RIGHT:
            self.BOX_START -= Model.MODEL_WIDTH / 40
            self.BOX_END -= Model.MODEL_WIDTH / 40
            if self.BOX_START <= 0 + Model.ALIEN_X_OFF:
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
            point_list = (
                (hitter[0], hitter[1] + self.bullet_height), (0, 0))  # Filler parameter used so
        elif hitter in self.alien_bullets:
            point_list = ((hitter[0], hitter[1]), (0, 0))
        else:
            return 0

        for point in point_list:
            if hitee.x <= point[0] <= hitee.x + hitee.width and hitee.y <= point[1] <= hitee.y + hitee.height:
                return True

    def player_edge_check(self):
        if self.player.x <= 0:
            if not self.player.dx >= 0:  # Stops infinite dx = 0 at edges
                self.player.dx = 0
        elif self.player.x + self.player.width >= Model.MODEL_WIDTH:
            if not self.player.dx <= 0:
                self.player.dx = 0

    def player_speed_trunc(self):
        if self.player.dx < 0:
            self.player.dx = -Model.PLAYER_SPEED
        elif self.player.dx > 0:
            self.player.dx = Model.PLAYER_SPEED

    def player_death_check(self, bullet=(0, 0)):
            for mob in self.objects[:]:
                if mob.y <= 0:  # Monsters off bottom edge of screen
                    return True

                elif mob.y <= self.player.y + self.player.height:
                    if self.hitbox_check(mob, self.player):
                        return True

            if self.hitbox_check(bullet, self.player):
                self.alien_bullets.remove(bullet)
                return True

    def screen_change(self):
        if self.player_lives == 0:
            self.events.append(GameEvent(GameEvent.EventType.GAME_OVER))  # game over screen
            self.game_over = True

        elif self.player.is_active and len(self.objects) == 0:  # Player defeated aliens
            self.events.append(GameEvent(GameEvent.EventType.NEXT_LEVEL))  # reset screen with next level, tick speed faster, more bullets from aliens

        elif not self.player.is_active:  # Aliens reach bottom of screen or Alien kill player
            self.player_lives -= 1
            self.events.append(GameEvent(GameEvent.EventType.LIFE_LOST, args=self.player_lives))  # reset same level, player_lives -= 1
            self.events.append(GameEvent(GameEvent.EventType.RESET_SCREEN))

    def alien_ending(self):  # TODO work out why aliens aren't leaving screen smoothly
        for mob in self.objects:
            if mob.y + mob.height <= 0:
                print(len(self.objects))
                self.objects.remove(mob)
            self.update_position(mob, 0, -Model.MODEL_HEIGHT / 20)

    def alien_bullet_update(self):
        for bullet in self.alien_bullets:
            bullet[1] -= self.bullet_dy

            if bullet[1] <= 0:
                self.alien_bullets.remove(bullet)

            if bullet[1] <= self.player.y + self.player.height and self.player_death_check(bullet):
                self.player.is_blown = True

    def bullet_update(self):
        for bullet in self.bullets:
            bullet[1] += self.bullet_dy

            if bullet[1] >= Model.MODEL_HEIGHT:
                self.bullets.remove(bullet)

            for mob in self.objects[:]:
                if self.hitbox_check(bullet, mob):
                    self.events.append(GameEvent(GameEvent.EventType.BLOOD_IMPACT,
                                                 (bullet[0], bullet[1] + self.bullet_height)))
                    self.objects.remove(mob)
                    self.bullets.remove(bullet)

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

    def update(self, dt):
        if self.player_death_check():
            self.player.is_blown = True
        self.screen_change()
        if self.tick % self.tick_speed == 0:
            self.tick = 0
            if not self.player.is_blown:
                self.alien_update()
            elif len(self.objects) > 0:
                self.events.append(GameEvent(GameEvent.EventType.EXPLOSION, (self.player.x + self.player.width / 2,
                                                                             self.player.y + self.player.height / 2)))
                self.alien_ending()
        if self.player.is_blown:
            self.player.img_name = "x-wing_burnt.png"
            if len(self.objects) == 0:
                self.player.is_active = False
        self.player_speed_trunc()
        self.player_edge_check()
        self.update_position(self.player, self.player.dx, self.player.dy)
        self.bullet_update()
        self.alien_bullet_update()
        self.timekeeper()

    def reset(self):
        pass

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

            elif key_val == key.LEFT:
                self.keys_pressed += 1
                if not self.player.x <= 0 and not self.player.dx < 0:
                    self.player.dx -= Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                self.keys_pressed += 1
                if not self.player.x + self.player.width >= Model.MODEL_WIDTH and not self.player.dx > 0:
                    self.player.dx += Model.PLAYER_SPEED

            elif key_val == key.Q and self.q_countdown <= 0:
                self.events.append(GameEvent(GameEvent.EventType.PLAYER_FIRE))
                print("Wow! The Q has been pressed")
                if len(self.bullets) < self.bullet_max:

                    self.bullets.append([self.player.x + x1_ship, self.player.y + y_ship])
                    self.q_countdown = self.countdown

            elif key_val == key.W and self.e_countdown <= 0:
                print("Wow! The E has been pressed")
                if len(self.bullets) < self.bullet_max:
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
            if key_val == key.LEFT:
                self.keys_pressed -= 1
                if not self.player.x <= 0 or not self.keys_pressed == 1 and not self.player.dx == 0:
                    self.player.dx += Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                self.keys_pressed -= 1
                if not self.player.x + self.player.width >= Model.MODEL_WIDTH or not self.keys_pressed == 1 and not self.player.dx == 0:
                    self.player.dx -= Model.PLAYER_SPEED


class Alien(GameObject):
    def __init__(self, x, y, width, height, img_name):
        super().__init__(x, y, width, height, img_name)
        self.dx = 1
