import math, random
import pyglet
import sys
from pyglet import graphics
from pyglet.graphics import Batch, GL_QUADS, GL_LINES, GL_TRIANGLE_FAN
from model import Model, GameModel, GameEvent, GameObject
import numpy as np
from frame import GameFrame, GameButton
from functools import partial
from enum import Enum

KEY_PRESS, KEY_RELEASE = 0, 1


class SpaceWindow(GameFrame):
    class Scene(Enum):
        PLAYING = 0
        MAIN_MENU = 1
        GAME_OVER = 2
        CLOSING = 3
        MAIN_TO_PLAYING = 4

    BULLET_HEIGHT_PERCENT = 0.015
    BULLET_RADIUS_PERCENT = 0.006
    MAIN_BTN_WIDTH_PERCENT, MAIN_BTN_HEIGHT_PERCENT, MAIN_BTN_LBLS_PADDING_Y_PERCENT = 0.25, 0.1, 0.1
    STAR_MOVE_SPEED = 3
    STAR_SIZE = 1
    COOLDOWN = 150

    def __init__(self, dev_mode=False):
        super(SpaceWindow, self).__init__(dev_mode)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.max_cooldown = SpaceWindow.COOLDOWN
        self.cooldown = self.max_cooldown
        self.menu_grad_motion = 0
        self.set_caption("Space Clone")
        pyglet.font.add_file('res/8-BIT WONDER.ttf')
        self.bit_font = pyglet.font.load('8Bit Wonder')
        self.set_btns()
        self.head_lbl = None
        self.tick = 0
        self.img_base = dict()
        self.star_pts = []
        self.generate_stars()
        self.flame_colours = []
        self.rendered_sprite = []
        self.pixel_spills = []
        self.star_batch = []
        self.main_btns[0].func = partial(self.change_scene, self.Scene.MAIN_TO_PLAYING)

        self.reset_flame_colours()

    def get_btn_labels(self):
        return "START_GAME", "OPTIONS", "EXIT"

    def generate_stars(self):
        self.star_pts = []
        for i in range(0, 400):
            x = math.floor(random.random() * self.main_width)
            y = math.floor(random.random() * self.main_height)
            self.star_pts.extend([[x, y,
                                   x + SpaceWindow.STAR_SIZE, y,
                                   x + SpaceWindow.STAR_SIZE, y + SpaceWindow.STAR_SIZE,
                                   x, y + SpaceWindow.STAR_SIZE]])

    def update_stars(self):
        for i, val in enumerate(self.star_pts):
            is_loop = False
            to_move = SpaceWindow.STAR_MOVE_SPEED
            if self.scene == self.Scene.MAIN_TO_PLAYING:
                to_move = (self.cooldown / SpaceWindow.COOLDOWN) * SpaceWindow.STAR_MOVE_SPEED
            if self.star_pts[i][2] + to_move >= self.width - SpaceWindow.STAR_SIZE:
                is_loop = True
            for j in range(0, len(self.star_pts[i]), 2):
                self.star_pts[i][j] = (self.star_pts[i][j] + to_move)
                if is_loop:
                    self.star_pts[i][j] -= self.width

    def draw_stars(self):
        star_batch = Batch()
        for i in self.star_pts:
            star_batch.add(4, GL_QUADS, None, ('v2f', i))
        star_batch.draw()

    def draw_game_screen(self):
        if self.scene == self.Scene.PLAYING:
            self.clear()
            self.draw_stars()
            ship = self.model.player
            self.draw_lasers()
            if ship.is_active:
                self.draw_flame(self.to_screen_x(ship.x), self.to_screen_y(ship.y), self.to_screen_x(ship.width))
            self.draw_sprite_objs()
            self.draw_pixel_spills()
            self.draw_header()
            if GameFrame.dev_mode:
                self.fps_display.draw()
            self.tick += 1
        elif self.scene == self.Scene.MAIN_TO_PLAYING:
            self.clear()
            self.draw_stars()
            self.draw_header()
            self.draw_main_btns()
        elif self.scene == self.Scene.GAME_OVER:
            lrg_txt_size = self.main_width // 30
            small_txt_size = self.main_width // 50
            y_padding = small_txt_size
            origin_y = 0.6 * self.height
            self.game_over_lbl = pyglet.text.Label(
                "You Lose Idiot",
                font_name='8Bit Wonder',
                font_size=lrg_txt_size,
                width=self.main_width // 4, height=self.header_height * 2,
                x=self.main_width // 2, y=origin_y,
                anchor_x='center', anchor_y='center',
                color=(255, 255, 255, 255))
            y_add = lrg_txt_size + y_padding
            self.control_lbl_space = pyglet.text.Label("Space to Exit.",
                                                                            font_name='8Bit Wonder',
                                                                            font_size=small_txt_size,
                                                                            width=self.main_width // 4,
                                                                            height=self.header_height * 2,
                                                                            x=self.main_width // 2,
                                                                            y=origin_y - y_add,
                                                                            anchor_x='center', anchor_y='center',
                                                                            color=(255, 255, 255, 255))
            y_add += small_txt_size
            self.control_lbl_r = pyglet.text.Label("R to retry",
                                                                        font_name='8Bit Wonder',
                                                                        font_size=small_txt_size,
                                                                        width=self.main_width // 4,
                                                                        height=self.header_height,
                                                                        x=self.main_width // 2,
                                                                        y=origin_y - y_add,
                                                                        anchor_x='center', anchor_y='center',
                                                                        color=(255, 255, 255, 255))
            self.game_over_lbl.draw()
            self.control_lbl_space.draw()
            self.control_lbl_r.draw()

    def draw_main_menu_background(self):
        self.draw_stars()

    def trigger_events(self):
        events = self.model.get_game_events()
        for ev in events:
            if ev.type == GameEvent.EventType.BLOOD_IMPACT:
                colour = 4 * PixelSpillBlock.BLOOD_COLOUR
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         [colour], 0.5, 1)
            elif ev.type == GameEvent.EventType.EXPLOSION:
                colours = [4 * col for col in PixelSpillBlock.FLAME_COLOURS]
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         colours, 1, 0.66)
            elif ev.type == GameEvent.EventType.GAME_OVER:
                self.change_scene(self.Scene.GAME_OVER)
            elif ev.type == GameEvent.EventType.RESET:
                self.reset()
            if not GameFrame.dev_mode and hasattr(ev, 'sound') and ev.sound is not None:
                self.play_sound(ev.sound)
            print("Event recieved: ", ev.type)
            self.model.events = []

    def set_model(self):
        self.model = Model()

    def reset(self):
        self.set_model()
        self.pixel_spills = []
        self.change_scene(self.Scene.MAIN_MENU)

    def trigger_pixel_spill(self, src_x, src_y, colours, circ_range_ratio, speed_ratio):
        start = 0
        for theta in np.linspace(start, start + circ_range_ratio * 2 * math.pi, num=40):
            ran_x = random.randint(0, 15)
            ran_y = random.randint(0, 15)
            self.pixel_spills.append(PixelSpillBlock(src_x + ran_x, src_y + ran_y, theta,
                                                     colours[random.randint(0, len(colours) - 1)],
                                                     speed=speed_ratio, size=1))

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
        objs = [self.model.player]
        objs.extend(self.model.objects)
        for obj in objs:
            if obj.is_active:
                sprite = self.get_rendered_sprite(obj, sprite_batch)
                self.rendered_sprite.append(sprite)

        sprite_batch.draw()

    def get_rendered_sprite(self, obj: GameObject, sprite_batch: Batch):
        if obj.img_name not in self.img_base.keys():
            img_path = "img/" + obj.img_name
            stream = open(img_path, 'rb')
            self.img_base[obj.img_name] = pyglet.image.load(img_path, file=stream)
        sprite = pyglet.sprite.Sprite(img=self.img_base[obj.img_name], batch=sprite_batch)
        sprite.x = self.main_width * (obj.x / self.model.MODEL_WIDTH)
        sprite.y = self.main_height * (obj.y / self.model.MODEL_HEIGHT)

        tgt_x = obj.width / self.model.MODEL_WIDTH
        tgt_y = obj.height / self.model.MODEL_HEIGHT
        sprite.scale_x = tgt_x * self.main_width / sprite.width
        sprite.scale_y = tgt_y * self.height / sprite.height
        return sprite

    def draw_pixel_spills(self):
        pxl_batch = Batch()
        for px in self.pixel_spills:
            px.update(self.tick)
        self.pixel_spills[:] = [val for val in self.pixel_spills if not val.is_vanished]
        num_of = 0
        px_vertices = []
        colours = []
        for px in self.pixel_spills:
            num_of += 4
            px_vertices.extend((px.x, px.y, px.x, px.y + px.size,
                                px.x + px.size, px.y + px.size, px.x + px.size, px.y))
            colours.extend(px.colour)
        pxl_batch.add(num_of, GL_QUADS, None, ('v2f', px_vertices), ('c3B', colours))
        pxl_batch.draw()

    def draw_flame(self, x, y, width):
        flame_height = (self.main_height + self.main_width) // 75
        rocket_width = width // 8
        flame_width_reduct = rocket_width // 8
        offset = 7.5 * width // 32
        padding = (width * 14 // 32)

        if random.random() < 0.2:
            self.reset_flame_colours()

        flame_batch = Batch()
        srcs = [[x + offset + i * padding, x + offset + rocket_width + i * padding] for i in range(0, 2)]
        for i, [src_x1, src_x2] in enumerate(srcs):
            flame_batch.add(4, GL_QUADS, None,
                            ('v2f', [src_x1, y, src_x1 + flame_width_reduct, y - flame_height,
                                     src_x2 - flame_width_reduct, y - flame_height, src_x2, y]),
                            ('c3B', self.flame_colours[i]))
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
        complement = 255 - self.alpha
        header_batch = Batch()
        colors = (0, 0, 0, complement,
                  13, 22, 48, complement,
                  13, 22, 48, complement,
                  0, 0, 0, complement)
        header_batch.add(4, GL_QUADS, None, ('v2f', [0, self.main_height,
                                                     0, self.main_height + self.header_height,
                                                     self.main_width, self.main_height + self.header_height,
                                                     self.main_width, self.main_height]), ('c4B', colors))
        header_batch.add(2, GL_LINES, None, ('v2f', [0, self.main_height,
                                                     self.main_width, self.main_height]),
                         ('c4B', 2 * (255, 255, 255, complement)))
        header_batch.draw()
        self.head_lbl = pyglet.text.Label("Enemies Remaining:",
                                          font_name='8Bit Wonder',
                                          font_size=self.main_width // 50,
                                          width=self.main_width, height=self.header_height,
                                          x=self.main_width // 40, y=self.main_height + self.header_height,
                                          anchor_x='left', anchor_y='top',
                                          color=(255, 255, 255, complement))
        self.head_lbl.draw()

    def update(self, dt):
        if self.scene == self.Scene.MAIN_MENU:
            self.update_stars()
        elif self.scene == self.Scene.CLOSING:
            self.close()
        elif self.scene == self.Scene.PLAYING:
            self.alpha = 0
            if not self.model:
                self.reset()
            self.model.update(dt)
            self.trigger_events()
        elif self.scene == self.Scene.MAIN_TO_PLAYING:
            for btn in self.main_btns:
                self.alpha = int(255 * (self.cooldown / self.max_cooldown))
                btn.change_alpha(self.alpha)
                if self.cooldown >= 0:
                    self.cooldown -= 1
                else:
                    self.change_scene(self.Scene.PLAYING)
            self.update_stars()
        elif self.scene == self.Scene.GAME_OVER:
            self.trigger_events()

    def play_main_menu_music(self):
        self.main_menu_song = pyglet.media.load("audio/space_clones.mp3", streaming=False).play()

    def play_sound(self, sound_name: str):
        src = pyglet.media.load("audio/" + sound_name)
        src.play()

    def change_scene(self, scene):
        if not self.scene or self.scene != scene:
            if scene == self.Scene.PLAYING:
                self.alpha = 0
                self.cooldown = self.COOLDOWN
                if not GameFrame.dev_mode:
                    self.set_mouse_visible(False)
                    if self.main_menu_song is not None:
                        self.main_menu_song.pause()
                        self.main_menu_song.delete()
                        self.main_menu_song = None
                if not self.model:
                    self.set_model()
            elif scene == self.Scene.MAIN_TO_PLAYING:
                self.set_mouse_visible(False)
                self.cooldown = self.COOLDOWN
            elif self.Scene.MAIN_MENU:
                self.alpha = 255
                self.set_mouse_visible(True)
            print("Screen scene: change: ", self.scene, "->", scene)
            self.scene = scene


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

    def __init__(self, x, y, vect, colour=None, speed=1, size=1):
        self.speed = self.MAX_SPEED * speed
        self.x = x
        self.y = y
        self.vect = vect
        self.size = self.DEF_SIZE
        self.dx = 1
        self.is_vanished = False
        self.colour = (self.DEF_COLOUR if colour is None else colour)
        self.size = PixelSpillBlock.DEF_SIZE + size

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
    print("System arguments:", sys.argv)
    window = SpaceWindow(True if len(sys.argv) > 1 and str(sys.argv[1]).lower() == "true" else False)
    pyglet.clock.set_fps_limit(60)
    delta = 1.0 / 60
    pyglet.clock.schedule_interval(window.update, delta)
    pyglet.app.run()
