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

        def alien_movement(self):
            pass


class Model:
    tick_speed = 60
    MODEL_WIDTH = 800
    MODEL_HEIGHT = 600
    PLAYER_SPEED = MODEL_WIDTH / 400
    ALIEN_WIDTH = MODEL_WIDTH / 20
    ALIEN_HEIGHT = MODEL_HEIGHT / 10
    ALIEN_Y_OFF = MODEL_HEIGHT / 30     # Offset from top of screen.
    ALIEN_X_OFF = MODEL_WIDTH / 40      # Offset from side of screen.
    BOX_START = ALIEN_X_OFF * 3                 # Box keeps track of alien block start and end point for edge detection
    BOX_END = MODEL_WIDTH - MODEL_WIDTH / 10    # Box end found using final alien spawn x pos + ALIEN_WIDTH taken from
                                                # Window width, final alien x pos found with print statements.

    def __init__(self):
        self.tick = 1
        self.ALIEN_MOVE_RIGHT = False
        self.bullets = []
        self.bullet_max = 4
        self.bullet_height = 30
        self.bullet_dy = 4
        self.objects = []   # list of Game Objects, will automatically draw on screen
        self.objects += [GameObject(self.MODEL_WIDTH / 2, self.MODEL_WIDTH / 20,
                                    self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "x-wing.png")]
        self.player = self.objects[0]
        print(self.player.__dict__)

        alien_y = self.MODEL_HEIGHT - self.ALIEN_Y_OFF - self.ALIEN_HEIGHT  # Alien spawn y starting point.
        while alien_y > self.MODEL_HEIGHT / 2:                              # Alien y spawn endpoint.
            alien_x = self.BOX_START                                  # Alien spawn x starting point.
            while alien_x < self.MODEL_WIDTH - self.ALIEN_X_OFF * 4:        # Alien x spawn endpoint.
                self.objects += [Alien(alien_x, alien_y, self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "alien.png")]
                alien_x += self.ALIEN_WIDTH * 1.5                           # Next alien spawn in row.
                print(alien_x + Model.ALIEN_WIDTH)
            alien_y -= self.ALIEN_HEIGHT * 1.3                              # Next alien spawn in column.

    def alien_update(self):
        if self.ALIEN_MOVE_RIGHT:
            Model.BOX_START += Model.MODEL_WIDTH / 40
            Model.BOX_END += Model.MODEL_WIDTH / 40
            if Model.BOX_END >= Model.MODEL_WIDTH:
                print('Deadly Jamedley')
                for obj in self.objects[1:]:
                    obj.dx = 0
                    obj.y -= Model.ALIEN_HEIGHT
                    self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                for obj in self.objects[1:]:
                    obj.x += Model.MODEL_WIDTH / 40

        elif not self.ALIEN_MOVE_RIGHT:
            Model.BOX_START -= Model.MODEL_WIDTH / 40
            Model.BOX_END -= Model.MODEL_WIDTH / 40
            if Model.BOX_START <= 0:
                print('Holy jamoley!')
                for obj in self.objects[1:]:
                    obj.dx = 0
                    obj.y -= Model.ALIEN_HEIGHT
                    self.ALIEN_MOVE_RIGHT = not self.ALIEN_MOVE_RIGHT
            else:
                for obj in self.objects[1:]:
                    obj.x -= Model.MODEL_WIDTH / 40

    def player_edge_det(self):
        if self.player.x <= 0:
            if self.player.dx == 0:    # Stops infinite dx = 0 at edges
                pass
            else:
                self.player.dx = 0
        elif self.player.x + self.player.width >= Model.MODEL_WIDTH:
            if self.player.dx == 0:
                pass
            else:
                self.player.dx = 0

    def player_speed_trunc(self):
        if self.player.dx < 0:
            self.player.dx = -Model.PLAYER_SPEED
        elif self.player.dx > 0:
            self.player.dx = Model.PLAYER_SPEED

    def update(self):
        if self.tick % Model.tick_speed == 0:
            self.alien_update()

        if abs(self.player.dx) > Model.PLAYER_SPEED:
            self.player_speed_trunc()

        self.player.x += self.player.dx
        #player.y += player.dy

        for obj in self.bullets:
            obj[1] += self.bullet_dy
            if obj[1] >= Model.MODEL_HEIGHT:
                self.bullets.remove(obj)
                print(self.bullets)


        self.player_edge_det()
        self.tick += 1

    def action(self, key_val: str, action_type: int):
        import view  # avoids circular imports

        if action_type == view.KEY_PRESS:
            print(key_val, " was pressed")
            if key_val == key.LEFT:
                if self.player.x <= 0 and self.player.dx != 0:
                    pass
                else:
                    self.player.dx -= Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                if self.player.x + self.player.width >= Model.MODEL_WIDTH and self.player.dx != 0:
                    pass
                else:
                    self.player.dx += Model.PLAYER_SPEED
            elif key_val == key.SPACE:
                print("Wow! The spacebar has been pressed")
                if len(self.bullets) < self.bullet_max:
                    self.bullets += [[self.player.x + self.player.width / 2, self.player.y + self.player.height]]

        if action_type == view.KEY_RELEASE:
            print(key_val, " was pressed")
            if key_val == key.LEFT:
                if self.player.x <= 0:
                    pass
                else:
                    self.player.dx += Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                if self.player.x + self.player.width >= Model.MODEL_WIDTH:
                    pass
                else:
                    self.player.dx -= Model.PLAYER_SPEED