import pyglet
from pyglet.window import key
import math
from model import Model, GameObject
import pyglet.graphics as graphics
import random
import simpleaudio as sa

KEY_PRESS, KEY_RELEASE = 0, 1

class SpaceWindow(pyglet.window.Window):
    WINDOW_WIDTH = 1700
    WINDOW_HEIGHT = 800
    SOUND_NAMES = ["laser_default"]
    TEST_SOUND_ON = False

    def __init__(self):
        super(SpaceWindow, self).__init__(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.img_base = dict()
        self.model = Model()
        self.fps_display = pyglet.clock.ClockDisplay()
        self.x = 0
        self.y = 0
        self.flame_colours = []
        self.reset_flame_colours()
        self.batch = graphics.Batch()
        self.rendered_sprite = []
        self.tick = 0
        self.sounds = {}
        self.load_sounds()


    def reset(self):
        pass

    def on_draw(self):
        if self.tick % 1000 == 0 and self.TEST_SOUND_ON:
            play_obj = self.sounds["laser_default"].play()
        self.batch = graphics.Batch()
        window.clear()
        self.rendered_sprite = []
        for obj in self.model.objects:
            if obj.img_name not in self.img_base.keys():
                img_path = "img/" + obj.img_name
                stream = open(img_path, 'rb')
                img = pyglet.image.load(img_path, file=stream)
                self.img_base[obj.img_name] = img
            sprite = pyglet.sprite.Sprite(img=self.img_base[obj.img_name], batch=self.batch)
            sprite.x = self.width * (obj.x / self.model.MODEL_WIDTH)
            sprite.y = self.height * (obj.y / self.model.MODEL_HEIGHT)

            tgt_x = obj.width / self.model.MODEL_WIDTH
            tgt_y = obj.height / self.model.MODEL_HEIGHT
            sprite.scale_x = tgt_x * self.width / sprite.width
            sprite.scale_y = tgt_y * self.height / sprite.height
            self.rendered_sprite.append(sprite)

        ship = self.model.objects[0]
        self.draw_flame(self.to_screen_x(ship.x), self.to_screen_y(ship.y), self.to_screen_x(ship.width),
                        self.to_screen_y(ship.height))
        for bullet in self.model.bullets:
            graphics.draw(2, graphics.GL_LINES,
                          ('v2f', [self.to_screen_x(bullet[0]),
                                   self.to_screen_y(bullet[1]),
                                   self.to_screen_x(bullet[0]),
                                   self.to_screen_y(bullet[1] + self.to_screen_y(self.model.bullet_height))]))
        self.batch.draw()

        self.tick += 1



    def on_key_press(self, symbol, modifiers):
        self.model.action(symbol, KEY_PRESS)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.close()
        else:
            self.model.action(symbol, KEY_RELEASE)

    def draw_flame(self, x, y, width, height):
        rocket_width = width // 8
        offset = 7.5 * width // 32
        flame_height = 40
        flame_width = 5
        if random.random() < 0.2:
            self.reset_flame_colours()
        # draw flame one
        src_x1 = x + offset
        src_x2 = x + offset + rocket_width
        graphics.draw(4, graphics.GL_QUADS,
                      ('v2f', [src_x1, y, src_x1, y - flame_height,
                               src_x2, y - flame_height, src_x2, y]),
                      ('c3B', self.flame_colours[0]))
        src_x1 = src_x1 + width * 14 // 32
        src_x2 = src_x2 + width * 14 // 32
        graphics.draw(4, graphics.GL_QUADS,
                      ('v2f', [src_x1, y, src_x1, y - flame_height,
                               src_x2, y - flame_height, src_x2, y]),
                      ('c3B', self.flame_colours[1]))

    def draw_laser(self, x, y):
        laser_scope_width = 7
        laser_scope_height = 60
        col = (255, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0)
        for i in range(0, 8):
            ran_x = [random.randint(x, x + laser_scope_width) for j in range(0, 4)]
            ran_y = [random.randint(y, y + laser_scope_height) for j in range(0, 4)]
            pts = [ran_x[j // 2] if j % 2 == 0 else ran_y[j // 2] for j in range(0, 8)]
            graphics.draw(4, graphics.GL_QUADS,
                          ('v2f', pts),
                          ('c3B', col))

    def update(self, dt):
        self.model.update()

    def to_screen_x(self, mod_x: list):
        return self.WINDOW_WIDTH * (mod_x / self.model.MODEL_WIDTH)

    def to_screen_y(self, mod_y: list):
        return self.WINDOW_HEIGHT * (mod_y / self.model.MODEL_HEIGHT)

    def reset_flame_colours(self):
        self.flame_colours = []
        variation_blue = 255
        blue_val_1 = 255 - random.randint(0, variation_blue)
        blue_val_2 = 255 - random.randint(0, variation_blue)
        self.flame_colours.append(tuple([255, 255, 255, 0, 0, blue_val_1,
                              0, 0, blue_val_2, 255, 255, 255]))
        blue_val_1 = 255 - random.randint(0, variation_blue)
        blue_val_2 = 255 - random.randint(0, variation_blue)
        self.flame_colours.append(tuple([255, 255, 255, 0, 0, blue_val_1,
                                 0, 0, blue_val_2, 255, 255, 255]))

    def load_sounds(self):
        for name in self.SOUND_NAMES:
            self.sounds[name] = sa.WaveObject.from_wave_file("audio/" + name + ".wav")

if __name__ == '__main__':
    window = SpaceWindow()
    pyglet.clock.set_fps_limit(60)
    dt = 1.0 / 60
    pyglet.clock.schedule_interval(window.update, dt)
    pyglet.app.run()

