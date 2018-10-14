import pyglet
from pyglet.window import key
import math


class BreakoutWindow(pyglet.window.Window):


    def __init__(self):
        pass

    def reset(self):
        pass

    def on_draw(self):
        window.clear()
        pass

    def on_key_press(self, symbol, modifiers):
        pass

    def on_key_release(self, symbol, modifiers):
        pass
        if symbol == key.ESCAPE:
            self.close()

    def update(self, dt):
        pass

if __name__ == '__main__':
    window = BreakoutWindow()
    pyglet.clock.set_fps_limit(400)
    dt = 1.0 / 60
    pyglet.clock.schedule_interval(window.update, dt)
    pyglet.app.run()

