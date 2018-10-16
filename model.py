from pyglet.window import key


class GameObject:
    def __init__(self, x, y, width, height, img_name):
        self.x = x  # x-coordinate from 0 to MODEL_WIDTH
        self.y = y  # y-coordinate from 0 to MODEL_HEIGHT
        self.img_name = img_name  # file name without folder dir (img) but with the extension (.pgn, .jpg etc)
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
    MODEL_WIDTH = 800
    MODEL_HEIGHT = 600
    PLAYER_SPEED = MODEL_WIDTH / 400
    ALIEN_WIDTH = MODEL_WIDTH / 20
    ALIEN_HEIGHT = MODEL_HEIGHT / 10
    ALIEN_Y_OFF = MODEL_HEIGHT / 30
    ALIEN_X_OFF = MODEL_WIDTH / 40

    def __init__(self):
        self.objects = [] # list of Game Objects, will automatically draw on screen

        # x and y adjusted to screen in view, consider relative to model size
        self.objects += [GameObject(self.MODEL_WIDTH / 2, 0, self.MODEL_WIDTH / 20, self.MODEL_HEIGHT / 10, "x-wing.png")]

        alien_y = self.MODEL_HEIGHT - self.ALIEN_Y_OFF - self.ALIEN_HEIGHT
        while alien_y > self.MODEL_HEIGHT / 2:
            alien_x = self.ALIEN_X_OFF
            while alien_x < self.MODEL_WIDTH - self.ALIEN_X_OFF:
                self.objects += [Alien(alien_x, alien_y, self.ALIEN_WIDTH, self.ALIEN_HEIGHT, "alien.png")]
                alien_x += self.ALIEN_WIDTH
            alien_y -= self.ALIEN_HEIGHT
    def update(self):
        # updates the state of the model

        # Sample code that moves the first game object by its velocity
        self.objects[0].x += self.objects[0].dx
        self.objects[0].y += self.objects[0].dy
        #for i in range(1, len(self.objects)):
        #   self.objects[i].x += self.objects[i].dx

    def action(self, key_val: str, action_type: int):
        # action_types integer constants: Press (view.KEY_PRESS), Release (view.KEY_RELEASE)
        # key val are constants defined in pyglet.window.key (as key)
        # Sample code which prints messages in reaction to a key press or release
        import view  # avoids circular imports
        if action_type == view.KEY_PRESS:
            print(key_val, " was pressed")
            if key_val == key.LEFT:
                self.objects[0].dx -= Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                self.objects[0].dx += Model.PLAYER_SPEED

        elif action_type == view.KEY_RELEASE:
            print(key_val, " was released")
            if key_val == key.LEFT:
                self.objects[0].dx += Model.PLAYER_SPEED
            elif key_val == key.RIGHT:
                self.objects[0].dx -= Model.PLAYER_SPEED
            elif key_val == key.SPACE:
                print("Wow! The spacebar has been released")

