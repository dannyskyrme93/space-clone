from pyglet.window import key

class GameObject:
    def __init__(self, x, y, width, height, img_name):
        self.x = x  # x-coordinate from 0 to MODEL_WIDTH
        self.y = y  # y-coordinate from 0 to MODEL_HEIGHT
        self.img_name = img_name # file name without folder dir (img) or extension (.pgn, .jpg etc)
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

    def update(self):
        # updates the state of the model
        pass

    def key_passed(self, key_val: str):
        if key_val == key.E:
            print("E has been pressed")