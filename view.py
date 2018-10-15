import pyglet
from pyglet.window import key
import math
from model import Model, GameObject
import pyglet.graphics as graphics

KEY_PRESS, KEY_RELEASE = 0, 1

class SpaceWindow(pyglet.window.Window):
    WINDOW_WIDTH = 1700
    WINDOW_HEIGHT = 800

    def __init__(self):
        super(SpaceWindow, self).__init__(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.img_base = dict()
        self.model = Model()
        self.fps_display = pyglet.clock.ClockDisplay()
        self.x = 0
        self.y = 0

    def reset(self):
        pass

    def on_draw(self):
        window.clear()
        for img in self.model.objects:
            self.draw_object(img)

    def draw_object(self, obj: GameObject):
        if obj.img_name not in self.img_base.keys():
            img_path = "img/" + obj.img_name + '.jpg'
            stream = open(img_path, 'rb')
            img = pyglet.image.load(img_path, file=stream)
            self.img_base[obj.img_name] = img
        sprite = pyglet.sprite.Sprite(img=self.img_base[obj.img_name],
                                        x=self.width * (obj.x / self.model.MODEL_WIDTH),
                                        y=self.height * (obj.y / self.model.MODEL_HEIGHT))
        tgt_x = obj.width / self.model.MODEL_WIDTH
        tgt_y = obj.height / self.model.MODEL_HEIGHT
        sprite.scale_x = tgt_x * self.width / sprite.width
        sprite.scale_y = tgt_y * self.height / sprite.height
        sprite.draw()

    def on_key_press(self, symbol, modifiers):
        self.model.action(symbol, KEY_PRESS)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.close()
        else:
            self.model.action(symbol, KEY_RELEASE)

    def update(self, dt):
        self.model.update()


if __name__ == '__main__':
    window = SpaceWindow()
    pyglet.clock.set_fps_limit(400)
    dt = 1.0 / 60
    pyglet.clock.schedule_interval(window.update, dt)
    pyglet.app.run()

