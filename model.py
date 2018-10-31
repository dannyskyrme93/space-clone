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


class Model:
    tick = 1
    MODEL_WIDTH = 800
    MODEL_HEIGHT = 600
    PLAYER_SPEED = MODEL_WIDTH / 400
    ALIEN_WIDTH = MODEL_WIDTH / 20
    ALIEN_HEIGHT = MODEL_HEIGHT / 10
    ALIEN_Y_OFF = MODEL_HEIGHT / 30     # Offset from top of screen.
    ALIEN_X_OFF = MODEL_WIDTH / 40    # Offset from side of screen.

    def __init__(self):
        self.objects = []   # list of Game Objects, will automatically draw on screen
        self.objects += [GameObject(self.MODEL_WIDTH / 2, self.MODEL_WIDTH / 20,
                                    self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "x-wing.png")]

        alien_y = self.MODEL_HEIGHT - self.ALIEN_Y_OFF - self.ALIEN_HEIGHT  # Alien spawn y starting point.
        while alien_y > self.MODEL_HEIGHT / 2:                              # Alien y spawn endpoint.
            alien_x = self.ALIEN_X_OFF * 3                                  # Alien spawn x starting point.
            while alien_x < self.MODEL_WIDTH - self.ALIEN_X_OFF * 4:        # Alien x spawn endpoint.
                self.objects += [Alien(alien_x, alien_y, self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "alien.png")]
                alien_x += self.ALIEN_WIDTH * 1.5                           # Next alien spawn in row.
            alien_y -= self.ALIEN_HEIGHT * 1.3                              # Next alien spawn in column.

    def update(self):
        # updates the state of the model]
        player = self.objects[0]
        if Model.tick % 60 == 0:
            for obj in self.objects[1:]:
                obj.x += Model.MODEL_WIDTH / 40
                obj.y += obj.dy

        self.objects[0].x += self.objects[0].dx
        #self.objects[0].y += self.objects[0].dy
        if player.x <= 0:
            if player.dx == 0:
                pass
            else:
                player.dx = 0
        elif player.x + player.width >= Model.MODEL_WIDTH:
            if player.dx == 0:
                pass
            else:
                player.dx = 0
        Model.tick += 1

    def action(self, key_val: str, action_type: int):
        import view  # avoids circular imports
        player = self.objects[0]

        if action_type == view.KEY_PRESS:
            print(key_val, " was pressed")
            if key_val == key.LEFT:
                if player.x <= 0 and player.dx != 0:
                    pass
                else:
                    player.dx -= Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                if player.x + player.width >= Model.MODEL_WIDTH and player.dx != 0:
                    pass
                else:
                    player.dx += Model.PLAYER_SPEED

        if action_type == view.KEY_RELEASE:
            print(key_val, " was pressed")
            if key_val == key.LEFT:
                if player.x <= 0:
                    pass
                else:
                    player.dx += Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                if player.x + player.width >= Model.MODEL_WIDTH:
                    pass
                else:
                    player.dx -= Model.PLAYER_SPEED
            elif key_val == key.SPACE:
                print("Wow! The spacebar has been released")

