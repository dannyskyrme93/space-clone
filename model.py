class GameObject:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.dx = 0
        self.dy = 0
        self.is_active = True

class Model:
    def __init__(self):
        pass

    def update(self):
        pass