import math, random
import pyglet
from enum import Enum
from pyglet import graphics
from pyglet.window import key, Window, mouse
from pyglet.graphics import Batch, GL_QUADS, GL_LINES, GL_TRIANGLE_FAN
from model import Model, GameEvent
from functools import partial
import numpy as np

KEY_PRESS, KEY_RELEASE = 0, 1


class GameFrame(Window):
    class ScreenContext(Enum):
        PLAYING = 0
        MAIN_MENU = 1
        GAME_OVER = 2
        CLOSING = 3

    class KeyAction(Enum):
        KEY_PRESS, KEY_RELEASE = 0, 1

    main_width: int = 1700
    main_height: int = 800
    header_height: int = 50
    DEV_MODE = True

    def __init__(self):
        super(GameFrame, self).__init__(self.main_width, self.main_height + self.header_height, visible=False)
        self.set_caption("Space Clone")
        icon = pyglet.image.load('img/x-wing_icon.png')
        self.set_icon(icon)
        self.model = Model()
        self.screen_context = None
        if not self.DEV_MODE:
            self.set_context(SpaceWindow.ScreenContext.MAIN_MENU)
            self.set_fullscreen(True)
            self.main_width = self.width
            ratio = self.header_height / self.main_height
            self.header_height = math.floor(self.height * ratio)
            self.main_height = math.floor(self.height * (1 - ratio))
            self.play_main_menu_music()
        else:
            self.set_context(SpaceWindow.ScreenContext.PLAYING)
            self.fps_display = None
            self.set_location(220, 30)
            self.width = self.main_width
            self.height = self.main_height + self.header_height
        self.set_visible(True)

    def to_screen_x(self, mod_x):
        return self.main_width * mod_x // self.model.MODEL_WIDTH

    def to_screen_y(self, mod_y):
        return self.main_height * mod_y // self.model.MODEL_HEIGHT

    def on_key_press(self, symbol, modifiers):
        if self.screen_context != GameFrame.ScreenContext.MAIN_MENU:
            self.model.action(symbol, KEY_PRESS)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.close()
        elif self.screen_context != GameFrame.ScreenContext.MAIN_MENU:
            self.model.action(symbol, KEY_RELEASE)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT and self.screen_context == GameFrame.ScreenContext.MAIN_MENU:
            self.menu_mouse_action(x, y)

    def set_context(self, context):
        if context == GameFrame.ScreenContext.PLAYING and not GameFrame.DEV_MODE:
            self.set_mouse_visible(False)
        else:
            self.set_mouse_visible(True)
        self.screen_context = context

    def menu_mouse_action(self, x, y):
        @property
        def path(self):
            raise NotImplementedError

    def play_main_menu_music(self):
        @property
        def path(self):
            raise NotImplementedError


class SpaceWindow(GameFrame):
    TEST_SOUND_ON = False
    BULLET_HEIGHT_PERCENT = 0.015
    BULLET_RADIUS_PERCENT = 0.006
    MAIN_BTN_LBLS = ["START_GAME", "OPTIONS", "EXIT"]
    MAIN_BTN_CONTEXTS = [GameFrame.ScreenContext.PLAYING,
                         GameFrame.ScreenContext.MAIN_MENU,
                         GameFrame.ScreenContext.CLOSING]
    MAIN_BTN_WIDTH_PERCENT, MAIN_BTN_HEIGHT_PERCENT, MAIN_BTN_LBLS_PADDING_Y_PERCENT = 0.25, 0.1, 0.1

    def __init__(self):
        super(SpaceWindow, self).__init__()
        pyglet.font.add_file('res/8-BIT WONDER.ttf')
        self.bit_font = pyglet.font.load('8Bit Wonder')

        btn_width, btn_height = self.width * SpaceWindow.MAIN_BTN_WIDTH_PERCENT, \
                                self.height * SpaceWindow.MAIN_BTN_HEIGHT_PERCENT
        self.main_btns = [
            Button(SpaceWindow.MAIN_BTN_LBLS[y], self.width // 2, 0.8 * self.height - (y + 1) * btn_height -
                   y * self.height * SpaceWindow.MAIN_BTN_LBLS_PADDING_Y_PERCENT, btn_width, btn_height,
                   partial(self.set_context, SpaceWindow.MAIN_BTN_CONTEXTS[y]))
            for y in range(0, len(SpaceWindow.MAIN_BTN_LBLS))]
        self.head_lbl = None
        self.tick = 0
        self.img_base = dict()
        self.star_pts = []
        self.generate_stars()
        self.flame_colours = []
        self.rendered_sprite = []
        self.pixel_spills = []

        self.reset_flame_colours()

    def set_clock(self, clock):
        if self.DEV_MODE:
            self.fps_display = clock.ClockDisplay()

    def generate_stars(self):
        self.star_pts = []
        star_width = 1
        for i in range(0, 400):
            x = math.floor(random.random() * self.main_width)
            y = math.floor(random.random() * self.main_height)
            self.star_pts.extend({(x, y,
                                   x + star_width, y,
                                   x + star_width, y + star_width,
                                   x, y + star_width)})

    def draw_stars(self):
        star_batch = Batch()
        for i in self.star_pts:
            star_batch.add(4, GL_QUADS, None, ('v2f', i))
        star_batch.draw()

    def on_draw(self):
        self.trigger_events()
        self.model.events = []

        if self.screen_context == SpaceWindow.ScreenContext.PLAYING:
            window.clear()
            self.draw_stars()
            ship = self.model.player
            self.draw_lasers()
            self.draw_sprite_objs()
            if ship.is_active:
                self.draw_flame(self.to_screen_x(ship.x), self.to_screen_y(ship.y), self.to_screen_x(ship.width))
            self.draw_pixel_spills()
            self.draw_header()

            if self.DEV_MODE:
                self.fps_display.draw()
            self.tick += 1
        elif self.screen_context == SpaceWindow.ScreenContext.GAME_OVER:
            self.head_lbl = pyglet.text.Label("You Lose Idiot",
                                              font_name='8Bit Wonder',
                                              font_size=self.main_width // 30,
                                              width=self.main_width // 4, height=self.header_height * 2,
                                              x=self.main_width // 2, y=self.height // 2,
                                              anchor_x='center', anchor_y='center',
                                              color=(255, 255, 255, 255))
            self.head_lbl.draw()
        elif self.screen_context == SpaceWindow.ScreenContext.MAIN_MENU:
            self.draw_main_btns()

    def draw_main_btns(self):
        for btn in self.main_btns:
            graphics.draw(4, GL_QUADS, ['v2f', [btn.x - btn.width // 2, btn.y - btn.height // 2,
                                                btn.x - btn.width // 2, btn.y + btn.height // 2,
                                                btn.x + btn.width // 2, btn.y + btn.height // 2,
                                                btn.x + btn.width // 2, btn.y - btn.height // 2]],
                          ['c3B', Button.COLOR])
            btn_lbl = pyglet.text.Label(btn.lbl,
                                        font_name='8Bit Wonder',
                                        font_size=0.3 * btn.height,
                                        width=btn.width, height=0.5 * btn.height,
                                        x=btn.x, y=btn.y,
                                        anchor_x='center', anchor_y='center',
                                        color=(255, 255, 255, 255))
            btn_lbl.draw()

    def trigger_events(self):
        for ev in self.model.events:
            if ev.type == GameEvent.EventType.BLOOD_IMPACT:
                colour = 4 * PixelSpillBlock.BLOOD_COLOUR
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         [colour], 0.5, 1)
            elif ev.type == GameEvent.EventType.EXPLOSION:
                colours = [4 * col for col in PixelSpillBlock.FLAME_COLOURS]
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         colours, 1, 0.66)
            elif ev.type == GameEvent.EventType.GAME_OVER:
                print("Game Over")
                self.set_context(SpaceWindow.ScreenContext.GAME_OVER)
            elif ev.type == GameEvent.EventType.RESET:
                print("Reset")
                self.set_context(SpaceWindow.ScreenContext.PLAYING)

    def trigger_pixel_spill(self, src_x, src_y, colours, circ_range_ratio, speed_ratio):
        start = 0
        for theta in np.linspace(start, start + circ_range_ratio * 2 * math.pi, num=40):
            ran_x = random.randint(0, 15)
            ran_y = random.randint(0, 15)
            self.pixel_spills.append(PixelSpillBlock(src_x + ran_x, src_y + ran_y, theta,
                                                     colours[random.randint(0, len(colours) - 1)],
                                                     speed_ratio=speed_ratio))

    def reset_flame_colours(self):
        self.flame_colours = []
        variation_blue = 255
        for i in range(0, 2):
            blue_val_1 = 255 - random.randint(0, variation_blue)
            blue_val_2 = 255 - random.randint(0, variation_blue)
            self.flame_colours.append(tuple([255, 255, 255, 0, 0, blue_val_1, 0, 0, blue_val_2, 255, 255, 255]))

    def draw_sprite_objs(self):
        sprite_batch = Batch()
        self.rendered_sprite = []
        composite = [self.model.player]
        composite.extend(self.model.objects)
        for obj in composite:
            if obj.is_active:
                if obj.img_name not in self.img_base.keys():
                    img_path = "img/" + obj.img_name
                    stream = open(img_path, 'rb')
                    img = pyglet.image.load(img_path, file=stream)
                    self.img_base[obj.img_name] = img
                sprite = pyglet.sprite.Sprite(img=self.img_base[obj.img_name], batch=sprite_batch)
                sprite.x = self.main_width * (obj.x / self.model.MODEL_WIDTH)
                sprite.y = self.main_height * (obj.y / self.model.MODEL_HEIGHT)

                tgt_x = obj.width / self.model.MODEL_WIDTH
                tgt_y = obj.height / self.model.MODEL_HEIGHT
                sprite.scale_x = tgt_x * self.main_width / sprite.width
                sprite.scale_y = tgt_y * self.height / sprite.height
                self.rendered_sprite.append(sprite)

        sprite_batch.draw()

    def draw_pixel_spills(self):
        pxl_batch = Batch()
        for px in self.pixel_spills:
            px.update(self.tick)
        self.pixel_spills[:] = [val for val in self.pixel_spills if not val.is_vanished]
        for px in self.pixel_spills:
            colours = px.colour
            pxl_batch.add(4, GL_QUADS, None,
                          ('v2f', (px.x, px.y, px.x, px.y + px.size,
                                   px.x + px.size, px.y + px.size, px.x + px.size, px.y)),
                          ('c3B', colours)
                          )
        pxl_batch.draw()

    def draw_flame(self, x, y, width):
        rocket_width = width // 8
        offset = 7.5 * width // 32
        flame_height = (self.main_height + self.main_width) // 75
        flame_width_reduct = rocket_width // 8
        if random.random() < 0.2:
            self.reset_flame_colours()
        # draw flame one
        src_x1 = x + offset
        src_x2 = x + offset + rocket_width
        flame_batch = Batch()
        flame_batch.add(4, GL_QUADS, None,
                        ('v2f', [src_x1, y, src_x1 + flame_width_reduct, y - flame_height,
                                 src_x2 - flame_width_reduct, y - flame_height, src_x2, y]),
                        ('c3B', self.flame_colours[0]))
        src_x1 = src_x1 + width * 14 // 32
        src_x2 = src_x2 + width * 14 // 32
        flame_batch.add(4, GL_QUADS, None,
                        ('v2f', [src_x1, y, src_x1 + flame_width_reduct, y - flame_height,
                                 src_x2 - flame_width_reduct, y - flame_height, src_x2, y]),
                        ('c3B', self.flame_colours[1]))
        flame_batch.draw()

    def draw_lasers(self):
        colors = (0, 200, 255, 0, 200, 255)
        for bullet in self.model.bullets:
            graphics.draw(2, GL_LINES,
                          ('v2f', [self.to_screen_x(bullet[0]),
                                   self.to_screen_y(bullet[1]),
                                   self.to_screen_x(bullet[0]),
                                   self.to_screen_y(bullet[1] + int(self.BULLET_HEIGHT_PERCENT * self.main_height))]),
                          ('c3B', colors))
        radius = SpaceWindow.BULLET_RADIUS_PERCENT * self.width
        for x, y in self.model.alien_bullets:
            circ_pts = [self.to_screen_x(x), self.to_screen_y(y) + radius]
            for theta in np.linspace(0, 2 * math.pi, 40):
                error = random.randint(-1 * radius // 4, radius // 4)
                circ_pts.extend([circ_pts[0] + (radius + error) * math.sin(theta),
                                 circ_pts[1] + (radius + error) * math.cos(theta)])
            num_of_vert = (len(circ_pts) // 2)
            colors = [255, 255, 255]
            colors.extend((num_of_vert - 1) * [255, 0, 255])
            graphics.draw(num_of_vert, GL_TRIANGLE_FAN,
                          ('v2f', circ_pts),
                          ('c3B', colors))

    def draw_header(self):
        colors = [0, 0, 0, 13, 22, 48, 13, 22, 48, 0, 0, 0]
        graphics.draw(4, GL_QUADS, ('v2f', [0, self.main_height,
                                            0, self.main_height + self.header_height,
                                            self.main_width, self.main_height + self.header_height,
                                            self.main_width, self.main_height]), ('c3b', colors))
        graphics.draw(2, GL_LINES, ('v2f', [0, self.main_height,
                                            self.main_width, self.main_height]))
        self.head_lbl = pyglet.text.Label("Enemies Remaining:",
                                          font_name='8Bit Wonder',
                                          font_size=self.main_width // 50,
                                          width=self.main_width, height=self.header_height,
                                          x=self.main_width // 40, y=self.main_height + self.header_height,
                                          anchor_x='left', anchor_y='top',
                                          color=(255, 255, 255, 255))
        self.head_lbl.draw()

    def update(self, dt):
        if self.screen_context == GameFrame.ScreenContext.MAIN_MENU:
            pass
        elif self.screen_context == GameFrame.ScreenContext.CLOSING:
            self.close()
        else:
            self.model.update()

    def menu_mouse_action(self, x, y):
        if self.screen_context == GameFrame.ScreenContext.MAIN_MENU:
            for btn in self.main_btns:
                if btn.is_on(x, y):
                    btn.click()

    def play_main_menu_music(self):
        src = pyglet.media.load("audio/space_clones.mp3")
        src.play()

class PixelSpillBlock:
    DEF_COLOUR = (255, 255, 255)
    BLOOD_COLOUR = (102, 0, 0)
    FLAME_COLOURS = [(255, 91, 20),
                     (255, 35, 35),
                     (255, 162, 85)]
    MAX_SPEED = 3
    SIZE_DECAY: float = 0.2
    TICK_RATE = 2
    DEF_SIZE = 8

    def __init__(self, x, y, vect, colour=None, speed_ratio=1):
        self.speed = self.MAX_SPEED * speed_ratio
        self.x = x
        self.y = y
        self.vect = vect
        self.size = self.DEF_SIZE
        self.dx = 1
        self.is_vanished = False
        self.colour = (self.DEF_COLOUR if colour is None else colour)

    def update(self, dt):
        if dt % self.TICK_RATE != 0:
            return
        self.x += math.cos(self.vect) * self.speed
        self.y += math.sin(self.vect) * self.speed
        self.size -= self.SIZE_DECAY
        if self.size <= 0:
            self.is_vanished = True
            self.size = 0


class Button:
    COLOR = 4 * [125, 125, 125]

    def __init__(self, lbl, x, y, width, height, func):
        self.lbl = lbl
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.func = func

    def is_on(self, x, y):
        if self.x - self.width // 2 <= x <= self.x + self.width // 2 \
                and self.y - self.height // 2 <= y <= self.y + self.height // 2:
            return True
        return False

    def click(self):
        self.func()


if __name__ == '__main__':
    window = SpaceWindow()
    pyglet.clock.set_fps_limit(60)
    delta = 1.0 / 60
    window.set_clock(pyglet.clock)
    pyglet.clock.schedule_interval(window.update, delta)
    pyglet.app.run()
