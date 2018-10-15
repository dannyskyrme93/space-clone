from pyglet.window import key


class GameObject:
    def __init__(self, x, y, width, height, img_name):
        self.x = x  # x-coordinate from 0 to MODEL_WIDTH
        self.y = y  # y-coordinate from 0 to MODEL_HEIGHT
        self.img_name = img_name  # file name without folder dir (img) or extension (.pgn, .jpg etc)
        self.width = width
        self.height = height
        self.dx = 0
        self.dy = 0
        self.is_active = True


class Model:
    MODEL_WIDTH = 800
    MODEL_HEIGHT = 600

    def __init__(self):
        self.objects = [] # list of Game Objects, will automatically draw on screen

        # x and y adjusted to screen in view, consider relative to model size
        self.objects += [GameObject(50, 50, self.MODEL_WIDTH / 3, self.MODEL_HEIGHT / 2, "tom hanks")]
        self.objects[0].dx = 1  # sets tom hanks pic velocity to right at one pixel per update

    def update(self):
        # updates the state of the model

        # Sample code that moves the first game object by its velocity
        self.objects[0].x += self.objects[0].dx
        self.objects[0].y += self.objects[0].dy

    #
    def action(self, key_val: str, action_type: int):
        # action_types integer constants: Press (view.KEY_PRESS), Release (view.KEY_RELEASE)
        # key val are constants defined in pyglet.window.key (as key)

        # Sample code which prints messages in reaction to a key press or release
        import view  # avoids circular imports
        if action_type == view.KEY_PRESS:
            print(key_val, " was pressed")
        elif action_type == view.KEY_RELEASE:
            print(key_val, " was released")
            if key_val == key.SPACE:
                print("Wow! The spacebar has been released")

