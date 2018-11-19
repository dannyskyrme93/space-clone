import pyglet
from pyglet.window import key
import math
from model import Model, GameObject, GameEvent
import pyglet.graphics as graphics
import random
import simpleaudio as sa
import numpy as np

KEY_PRESS, KEY_RELEASE = 0, 1

class SpaceWindow(pyglet.window.Window):
    main_width = 1700
    main_height = 800
    header_height = 50
    SOUND_NAMES = ["laser_default"]
    TEST_SOUND_ON = False
    DEV_MODE = True
    BULLET_HEIGHT_PERCENT = 0.015

    def __init__(self):
        super(SpaceWindow, self).__init__(self.main_width, self.main_height + self.header_height)
        self.set_caption("Space Clone")
        icon = pyglet.image.load('img/x-wing_icon.png')
        self.set_icon(icon)
        if not self.DEV_MODE:
            self.set_fullscreen(True)
            self.main_width = self.width
            ratio = self.header_height / self.main_height
            self.header_height = math.floor(self.height * ratio)
            self.main_height = math.floor(self.height * (1 - ratio))
        else:
            self.fps_display = None
            self.set_location(50, 50)
            self.width = self.main_width
            self.height = self.main_height + self.header_height
        self.img_base = dict()
        self.model = Model()
        self.star_pts = []
        self.generate_stars()
        self.flame_colours = []
        self.reset_flame_colours()
        self.batch = graphics.Batch()
        self.rendered_sprite = []
        self.tick = 0
        self.sounds = {}
        self.load_sounds()
        self.pixel_spills = []

    def set_clock(self, clock:pyglet):
        if self.DEV_MODE:
            self.fps_display = clock.ClockDisplay()

    def reset(self):
        pass

    def generate_stars(self):
        num_of_pts = 100
        self.star_pts = []
        star_width = 1
        for i in range(0, 400):
            x = math.floor(random.random() * self.main_width)
            y = math.floor(random.random() * self.main_height)
            self.star_pts.extend([[x, y,
                               x + star_width, y,
                               x + star_width, y + star_width,
                               x, y + star_width]])

    def draw_stars(self):
        star_batch = graphics.Batch()
        colors = (102, 0, 0, 102, 0, 0, 102, 0, 0, 102, 0, 0)
        for i in self.star_pts:
            star_batch.add(4, graphics.GL_QUADS, None, ('v2f', i))
        star_batch.draw()

    def on_draw(self):
        if self.tick % 5000 == 0 and self.TEST_SOUND_ON:
            play_obj = self.sounds["laser_default"].play()
        self.trigger_events()
        self.model.events = []

        window.clear()

        self.batch = graphics.Batch()
        self.draw_stars()
        self.rendered_sprite = []
        ship = self.model.player
        obj: GameObject
        composite = [ship] + self.model.objects
        for obj in composite:
            if obj.is_active:
                if obj.img_name not in self.img_base.keys():
                    img_path = "img/" + obj.img_name
                    stream = open(img_path, 'rb')
                    img = pyglet.image.load(img_path, file=stream)
                    self.img_base[obj.img_name] = img
                sprite = pyglet.sprite.Sprite(img=self.img_base[obj.img_name], batch=self.batch)
                sprite.x = self.main_width * (obj.x / self.model.MODEL_WIDTH)
                sprite.y = self.main_height * (obj.y / self.model.MODEL_HEIGHT)

                tgt_x = obj.width / self.model.MODEL_WIDTH
                tgt_y = obj.height / self.model.MODEL_HEIGHT
                sprite.scale_x = tgt_x * self.main_width / sprite.width
                sprite.scale_y = tgt_y * self.height / sprite.height
                self.rendered_sprite.append(sprite)

        self.batch.draw()
        self.draw_lasers()
        if ship.is_active:
            self.draw_flame(self.to_screen_x(ship.x), self.to_screen_y(ship.y), self.to_screen_x(ship.width),
                            self.to_screen_y(ship.height))
        self.draw_pixel_spills()
        self.draw_header()

        if self.DEV_MODE:
            self.fps_display.draw()
        self.tick += 1

    def on_key_press(self, symbol, modifiers):
        self.model.action(symbol, KEY_PRESS)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.close()
        else:
            self.model.action(symbol, KEY_RELEASE)

    def trigger_events(self):
        ev: GameEvent
        for ev in self.model.events:
            if ev.type == "blood_impact":
                colour = PixelSpillBlock.BLOOD_COLOUR
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         [colour], 0.5, 1)
            elif ev.type == "explosion":
                colours = PixelSpillBlock.FLAME_COLOURS
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         colours, 1, 0.66)

    def draw_pixel_spills(self):
        pxl_batch = pyglet.graphics.Batch()
        for px in self.pixel_spills:
            px.update(self.tick)
        self.pixel_spills[:] = [val for val in self.pixel_spills if not val.is_vanished]
        px: PixelSpillBlock
        for px in self.pixel_spills:
            colours = px.colour
            pxl_batch.add(4, graphics.GL_QUADS, None,
                          ('v2f', (px.x, px.y, px.x, px.y + px.size,
                                   px.x + px.size, px.y + px.size, px.x + px.size, px.y)),
                          ('c3B', colours)
                          )
        pxl_batch.draw()

    def trigger_pixel_spill(self, src_x, src_y, colours, circ_range_ratio, speed_ratio):
        start = 0
        for theta in np.linspace(start, start + circ_range_ratio * 2 * math.pi, num=40):
            ran_x = random.randint(0, 15)
            ran_y = random.randint(0, 15)
            self.pixel_spills.append(PixelSpillBlock(src_x + ran_x, src_y + ran_y, theta,
                                                  colours[random.randint(0, len(colours) - 1)], speed_ratio=speed_ratio))

    def draw_flame(self, x, y, width, height):
        rocket_width = width // 8
        offset = 7.5 * width // 32
        flame_height = (self.main_height + self.main_width) // 75
        flame_width_reduct = rocket_width // 8
        if random.random() < 0.2:
            self.reset_flame_colours()
        # draw flame one
        src_x1 = x + offset
        src_x2 = x + offset + rocket_width
        flame_batch = pyglet.graphics.Batch()
        flame_batch.add(4, graphics.GL_QUADS, None,
                      ('v2f', [src_x1, y, src_x1 + flame_width_reduct, y - flame_height,
                               src_x2 - flame_width_reduct, y - flame_height, src_x2, y]),
                      ('c3B', self.flame_colours[0]))
        src_x1 = src_x1 + width * 14 // 32
        src_x2 = src_x2 + width * 14 // 32
        flame_batch.add(4, graphics.GL_QUADS, None,
                      ('v2f', [src_x1, y, src_x1 + flame_width_reduct, y - flame_height,
                               src_x2 - flame_width_reduct, y - flame_height, src_x2, y]),
                      ('c3B', self.flame_colours[1]))
        flame_batch.draw()

    def draw_lasers(self):
        colors = (0, 200, 255, 0, 200, 255)
        for bullet in self.model.bullets:
            graphics.draw(2, graphics.GL_LINES,
                          ('v2f', [self.to_screen_x(bullet[0]),
                                   self.to_screen_y(bullet[1]),
                                   self.to_screen_x(bullet[0]),
                                   self.to_screen_y(bullet[1] + int(self.BULLET_HEIGHT_PERCENT * self.main_height))]),
                          ('c3B', colors))

    def draw_header(self):
        colors = [0, 0, 0, 13, 22, 48, 13, 22, 48, 0, 0, 0]
        graphics.draw(4, graphics.GL_QUADS, ('v2f', [0, self.main_height,
                                                     0, self.main_height + self.header_height,
                                                     self.main_width, self.main_height + self.header_height,
                                                     self.main_width, self.main_height]), ('c3b', colors))
        graphics.draw(2, graphics.GL_LINES, ('v2f', [0, self.main_height,
                                                     self.main_width, self.main_height]))
        pyglet.font.add_file('res/8-BIT WONDER.ttf')
        bit_font = pyglet.font.load('8Bit Wonder')
        self.lbl = pyglet.text.Label("Enemies Remaining:",
                                     font_name='8Bit Wonder',
                                     font_size=self.main_width // 50,
                                     width=self.main_width, height=self.header_height ,
                                     x=self.main_width // 40, y=self.main_height + self.header_height,
                                     anchor_x='left', anchor_y='top',
                                     color=(255, 255, 255, 255))
        self.lbl.draw()

    def update(self, dt):
        self.model.update()

    def to_screen_x(self, mod_x: list):
        return self.main_width * (mod_x / self.model.MODEL_WIDTH)

    def to_screen_y(self, mod_y: list):
        return self.main_height * (mod_y / self.model.MODEL_HEIGHT)

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


class PixelSpillBlock:
    DEF_COLOUR = (255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255)
    BLOOD_COLOUR = (102, 0, 0, 102, 0, 0, 102, 0, 0, 102, 0, 0)
    FLAME_COLOURS = [(255, 91, 20, 255, 91, 20, 255, 91, 20, 255, 91, 20),
                     (255, 35, 35, 255, 35, 35, 255, 35, 35, 255, 35, 35),
                     (255, 162, 85, 255, 162, 85, 255, 162, 85, 255, 162, 85)]
    MAX_SPEED = 3
    SIZE_DECAY = 0.2
    TICK_RATE = 2
    DEF_SIZE = 6

    def __init__(self, x, y, vect, colour=None, speed_ratio=1):
        self.speed = self.MAX_SPEED * speed_ratio
        self.x = x
        self.y = y
        self.vect = vect
        self.size = self.DEF_SIZE
        self.dx = 1
        self.is_vanished = False
        self.colour = (self.DEF_COLOUR if colour == None else colour)

    def update(self, dt):
        if dt % self.TICK_RATE != 0:
            return
        self.x += math.cos(self.vect) * self.speed
        self.y += math.sin(self.vect) * self.speed
        self.size -= self.SIZE_DECAY
        if self.size <= 0:
            self.is_vanished = True
            self.size = 0


if __name__ == '__main__':
    window = SpaceWindow()
    pyglet.clock.set_fps_limit(60)
    dt = 1.0 / 60
    window.set_clock(pyglet.clock)
    pyglet.clock.schedule_interval(window.update, dt)
    pyglet.app.run()

