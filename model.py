from pyglet.window import key


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


class Alien(GameObject):
    def __init__(self, x, y, width, height, img_name):
        super().__init__(x, y, width, height, img_name)
        self.dx = 1


class GameEvent:
    EVENT_TYPES = ["blood_impact", "player_death"]

    def __init__(self, type_of, coordinates=None):
        self.type = type_of
        self.coordinates = coordinates


class Model:
    tick_speed = 30
    MODEL_WIDTH = 800
    MODEL_HEIGHT = 600
    PLAYER_SPEED = MODEL_WIDTH / 400
    ALIEN_WIDTH = MODEL_WIDTH / 25
    ALIEN_HEIGHT = MODEL_HEIGHT / 15
    ALIEN_Y_OFF = MODEL_HEIGHT / 30     # Offset from top of screen.
    ALIEN_X_OFF = MODEL_WIDTH / 40      # Offset from side of screen.

    def __init__(self):
        self.tick = 1
        self.ALIEN_MOVE_RIGHT = True
        self.bullets = []
        self.bullet_max = 4
        self.bullet_height = Model.MODEL_HEIGHT / 20
        self.bullet_dy = Model.MODEL_HEIGHT / 100
        self.shoot_count = True   # Which cannon to fire from next
        self.keys_pressed = 0
        self.events = []
        self.objects = []   # list of Game Objects, will automatically draw on screen
        self.player = GameObject(self.MODEL_WIDTH / 2, self.MODEL_WIDTH / 20,
                                 self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "x-wing.png")
        print(self.player.__dict__)

        alien_rows = 0
        alien_columns = 0
        alien_y = self.MODEL_HEIGHT - self.ALIEN_Y_OFF - self.ALIEN_HEIGHT          # Alien spawn y starting point.
        while alien_y > self.MODEL_HEIGHT / 2 and alien_rows < 4:                  # Alien y spawn endpoint.
            alien_x = Model.ALIEN_X_OFF * 3                                         # Alien spawn x starting point.
            while alien_x < self.MODEL_WIDTH - self.ALIEN_X_OFF * 4 and alien_columns < 15:   # Alien x spawn endpoint.
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

    def alien_update(self):
        if self.ALIEN_MOVE_RIGHT:
            self.BOX_START += Model.MODEL_WIDTH / 40
            self.BOX_END += Model.MODEL_WIDTH / 40
            if self.BOX_END >= Model.MODEL_WIDTH - Model.ALIEN_X_OFF:  # Checks if box is off screen also
                print('Deadly Jamedley')                                   # safety buffer
                for obj in self.objects[:]:
                    obj.dx = 0
                    obj.y -= Model.ALIEN_HEIGHT
                self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                for obj in self.objects[:]:
                    obj.x += Model.MODEL_WIDTH / 40

        elif not self.ALIEN_MOVE_RIGHT:
            self.BOX_START -= Model.MODEL_WIDTH / 40
            self.BOX_END -= Model.MODEL_WIDTH / 40
            if self.BOX_START <= 0 + Model.ALIEN_X_OFF:  #TODO
                print('Holy jamoley!')
                for obj in self.objects[:]:
                    obj.dx = 0
                    obj.y -= Model.ALIEN_HEIGHT
                self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                for obj in self.objects[:]:
                    obj.x -= Model.MODEL_WIDTH / 40

    def player_edge_det(self):
        if self.player.x <= 0:
            if not self.player.dx >= 0:    # Stops infinite dx = 0 at edges
                self.player.dx = 0
        elif self.player.x + self.player.width >= Model.MODEL_WIDTH:
            if not self.player.dx <= 0:
                self.player.dx = 0

    def player_speed_trunc(self):
        if self.player.dx < 0:
            self.player.dx = -Model.PLAYER_SPEED
        elif self.player.dx > 0:
            self.player.dx = Model.PLAYER_SPEED

    def update(self):
        for mob in self.objects[:]:
            if mob.y <= self.player.y + self.player.height:
                point_list = ((mob.x, mob.y), (mob.x + mob.width, mob.y), (mob.x, mob.y + mob.height),
                              (mob.x + mob.width, mob.y + mob.height))
                for point in point_list:
                    if self.player.x <= point[0] <= self.player.x + self.player.width and self.player.y <= point[1]:
                        self.player.is_active = False
                        self.events.append(GameEvent("player_death", (self.player.x + self.player.width / 2, self.player.y + self.player.height / 2)))

        if self.tick % Model.tick_speed == 0:
            self.alien_update()
        self.player_speed_trunc()
        self.player_edge_det()
        self.player.x += self.player.dx
        #player.y += player.dy

        for bullet in self.bullets:
            bullet[1] += self.bullet_dy

            if bullet[1] >= Model.MODEL_HEIGHT:
                self.bullets.remove(bullet)

            bullet_tip = (bullet[0], bullet[1] + self.bullet_height)
            for mob in self.objects[:]:
                if mob.x < bullet_tip[0] < mob.x + mob.width and mob.y < bullet_tip[1] < mob.y + mob.height:
                    self.events += [GameEvent("blood_impact", (bullet_tip[0], bullet_tip[1]))]
                    print(self.events)
                    self.objects.remove(mob)
                    self.bullets.remove(bullet)
        self.tick += 1

    def action(self, key_val: str, action_type: int):
        import view  # avoids circular imports
        x1_ship = self.player.width / 32
        x2_ship = self.player.width / float(1.04065)
        y_ship = self.player.height / 1.6
        if action_type == view.KEY_PRESS:
            print(key_val, " was pressed")
            if key_val == key.LEFT:
                if self.player.x <= 0 and self.player.dx < 0:
                    self.keys_pressed += 1
                else:
                    self.keys_pressed += 1
                    self.player.dx -= Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                if self.player.x + self.player.width >= Model.MODEL_WIDTH and self.player.dx > 0:
                    self.keys_pressed += 1
                else:
                    self.keys_pressed += 1
                    self.player.dx += Model.PLAYER_SPEED

            elif key_val == key.SPACE:
                print("Wow! The spacebar has been pressed")
                if len(self.bullets) < self.bullet_max:
                    if self.shoot_count:
                        self.bullets.append([self.player.x + x1_ship, self.player.y + y_ship])
                    elif not self.shoot_count:
                        self.bullets.append([self.player.x + x2_ship, self.player.y + y_ship])
                    self.shoot_count = not self.shoot_count

        if action_type == view.KEY_RELEASE:
            print(f"{key_val} was pressed")
            if key_val == key.LEFT:
                if self.player.x <= 0 or self.keys_pressed == 1 and self.player.dx == 0:
                    self.keys_pressed -= 1
                else:
                    self.keys_pressed -= 1
                    self.player.dx += Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                if self.player.x + self.player.width >= Model.MODEL_WIDTH or self.keys_pressed == 1 and self.player.dx == 0:
                    self.keys_pressed -= 1
                else:
                    self.keys_pressed -= 1
                    self.player.dx -= Model.PLAYER_SPEED
