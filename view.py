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
from abc import ABC, abstractmethod
from db_adapter import DataBaseAdapter
import os

KEY_PRESS, KEY_RELEASE = 0, 1

"""view.py: Front end."""

__author__ = "Daniel Skyrme, Joe Lovell"
__licence__ = "GNU General Public License v3.0"
__email__ = "danielskyrme@hotmail.com"
__credits__ = ["Joe Lovell"]


class SpaceWindow(GameFrame):
    class Scene(Enum):
        PLAYING = 0
        MAIN_MENU = 1
        GAME_OVER = 2
        CLOSING = 3
        MAIN_TO_PLAYING = 4
        NEXT_LEVEL = 5
        MAIN_MENU_WITH_OPTIONS = 6
        RESTART = 7
        DEV_RESET = 8
        PAUSED = 9

    class Sprites:
        PLAYER = "x-wing.png"
        ALIEN = "alien.png"
        PLAYER_BURNT = "x-wing_burnt.png"
        PLAYER_VERY_BURNT = "x-wing_very_burnt.png"
        PICKUP = "pickup.png"

        def get_sprite_names(self):
            return [self.PLAYER, self.ALIEN, self.PLAYER_BURNT, self.PLAYER_VERY_BURNT, self.PICKUP]

    BULLET_HEIGHT_PERCENT = 0.015
    BULLET_RADIUS_PERCENT = 0.006
    MAIN_BTN_WIDTH_PERCENT, MAIN_BTN_HEIGHT_PERCENT, MAIN_BTN_LBLS_PADDING_Y_PERCENT = 0.25, 0.1, 0.1
    STAR_MOVE_SPEED = 3
    STAR_SIZE = 1
    COOLDOWN = 120
    MAX_GLOW_INTENSITY = 200
    GLOW_INTENSITY_REDUCTION_RATE = 4

    def __init__(self, dev_mode=False):
        super(SpaceWindow, self).__init__(dev_mode)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.player_glow_colour = [255, 255, 255]
        self.max_cooldown = SpaceWindow.COOLDOWN
        self.cooldown = self.max_cooldown
        self.player_glow_intensity = 0
        self.menu_grad_motion = 0
        self.large_txt_size = self.main_width // 30
        self.medium_txt_size = self.main_width // 40
        self.small_txt_size = self.main_width // 50
        self.set_caption("Space Clone")
        self.head_lbl = None
        self.tick = 0
        self.img_base = dict()
        self.star_pts = []
        self.generate_stars()
        self.flame_colours = []
        self.rendered_sprite = []
        self.pixel_spills = []
        self.falling_parts = []
        self.pt_lbls = []
        self.star_batch = []
        self.main_btns[0].func = partial(self.change_scene, self.Scene.MAIN_TO_PLAYING)
        self.main_btns[1].func = partial(self.change_scene, self.Scene.MAIN_MENU_WITH_OPTIONS)
        self.main_btns[2].func = partial(self.change_scene, self.Scene.CLOSING)
        for btn in self.opt_btns:
            if btn.btn_group and btn.btn_group.parent == "SOUND" and not dev_mode:
                if btn.lbl.upper() == "ON":
                    btn.func = partial(lambda f, b: [f.settings.set_sound(b)], self, True)
                    btn.click()
                else:
                    btn.func = partial(lambda f, b: [f.settings.set_sound(b)], self, False)
                    self.settings.has_sound = False
            elif btn.lbl.upper() == "DEFAULT" and btn.btn_group.parent == "CONTROLS":
                btn.click()
        for btn in self.pause_btns:
            if btn.lbl == "CONTINUE":
                btn.func = partial(self.change_scene, self.Scene.PLAYING)
            elif btn.lbl == "RETRY":
                btn.func = self.clear_pts_and_restart
            if btn.lbl == "EXIT":
                btn.func = partial(self.change_scene, self.Scene.MAIN_MENU)
        self.reset_flame_colours()
        self.is_counting = False
        if dev_mode:
            self.settings.set_sound(False)
        else:
            self.settings.set_sound(True)

    def trigger_events(self):
        events = self.model.get_game_events()
        ev: GameEvent
        for ev in events:
            print("Event recieved: ", ev.type)
            if ev.type == GameEvent.EventType.ALIEN_DEATH:
                colour = 4 * PixelSpillBlock.BLOOD_COLOUR
                x, y = self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1])
                self.trigger_pixel_spill(x, y, [colour], 0.5, 1)
                self.trigger_pts_lbl(str(ev.args[0]), x, y)
            elif ev.type == GameEvent.EventType.EXPLOSION:
                colours = [4 * col for col in PixelSpillBlock.FLAME_COLOURS]
                self.trigger_pixel_spill(self.to_screen_x(ev.coordinates[0]), self.to_screen_y(ev.coordinates[1]),
                                         colours, 1, 0.66)
                self.player_glow_intensity = self.MAX_GLOW_INTENSITY
            elif ev.type == GameEvent.EventType.GAME_OVER:
                self.change_scene(self.Scene.GAME_OVER)
            elif ev.type == GameEvent.EventType.EXIT_MENU:
                self.exit_to_menu()
            elif ev.type == GameEvent.EventType.RESET_SCREEN:
                self.change_scene(self.Scene.RESTART)
            elif ev.type == GameEvent.EventType.NEXT_LEVEL:
                self.change_scene(self.Scene.NEXT_LEVEL)
            elif ev.type == GameEvent.EventType.PLAYER_DEATH:
                col = 4 * [80, 80, 80]
                self.trigger_falling_parts(self.to_screen_x(ev.coordinates[0]),
                                           self.to_screen_y(ev.coordinates[1]), col, self.model.player.width)
            elif ev.type == GameEvent.EventType.POWER_UP_COLLECT:
                self.pt_lbls.append(FadingPoints('1000', self.to_screen_x(ev.coordinates[0]),
                                                 self.to_screen_y(ev.coordinates[1])))
                self.player_glow_intensity = self.MAX_GLOW_INTENSITY
                self.player_glow_colour = [0, 0, 255]
            elif ev.type == GameEvent.EventType.GUN_JAM:
                self.player_glow_intensity = self.MAX_GLOW_INTENSITY
            if not GameFrame.dev_mode and hasattr(ev, 'sound') and ev.sound is not None:
                self.play_sound(ev.sound)
            self.model.events = []

    def change_scene(self, scene):
        if not self.scene or self.scene != scene:
            if scene == self.Scene.PLAYING:
                self.set_mouse_visible(True if GameFrame.dev_mode else False)
                self.pixel_spills = []
                self.falling_parts = []
                self.pts = []
                self.is_counting = False
                self.alpha = 0
                self.cooldown = self.COOLDOWN
                self.stop_music()
                if self.settings.has_sound:
                    self.set_mouse_visible(False)
                if not self.model:
                    self.set_model()
            elif scene == self.Scene.MAIN_TO_PLAYING:
                self.set_mouse_visible(True if GameFrame.dev_mode else False)
                self.is_counting = True
                self.cooldown = self.COOLDOWN
                self.model = Model()
            elif scene in {self.Scene.MAIN_MENU, self.Scene.MAIN_MENU_WITH_OPTIONS}:
                self.set_mouse_visible(True)
                if self.settings.has_sound and self.main_menu_song is None:
                    self.play_main_menu_music()
                self.is_counting = False
                self.alpha = 255
            elif scene == self.Scene.NEXT_LEVEL or scene == self.Scene.RESTART:
                self.set_mouse_visible(False)
                self.is_counting = True
                self.cooldown = self.COOLDOWN
            elif scene == self.Scene.PAUSED:
                self.set_mouse_visible(True)
            elif scene == self.Scene.CLOSING:
                sys.exit()
            self.scene = scene

    def update(self, dt):
        if self.player_glow_intensity > 0:
            self.player_glow_intensity -= self.GLOW_INTENSITY_REDUCTION_RATE
        for i in range(0, 3):
            if self.player_glow_colour[i] < 255:
                nxt = self.player_glow_colour[i] + 4
                self.player_glow_colour[i] = min(255, nxt)
        if self.cooldown >= 0 and self.is_counting:
            self.cooldown -= 1
        if self.scene in {self.Scene.MAIN_MENU, self.Scene.MAIN_MENU_WITH_OPTIONS}:
            self.update_stars()
        elif self.scene == self.Scene.PLAYING:
            self.alpha = 0
            self.model.update(dt)
            self.trigger_events()
        elif self.scene == self.Scene.MAIN_TO_PLAYING:
            for btn in self.main_btns:
                self.alpha = int(255 * (self.cooldown / self.max_cooldown))
                btn.change_alpha(self.alpha)
                if self.cooldown <= 0:
                    self.change_scene(self.Scene.PLAYING)
            self.update_stars()
        elif self.scene == self.Scene.GAME_OVER:
            self.trigger_events()
        elif self.scene == self.Scene.NEXT_LEVEL or self.scene == self.Scene.RESTART:
            difficulty = self.model.difficulty + 1 if self.scene == self.Scene.NEXT_LEVEL else 0
            if self.cooldown <= 0:
                self.model = Model(self.model.points, difficulty)
                self.change_scene(self.Scene.PLAYING)

    def set_model(self):
        self.model = Model()

    def exit_to_menu(self):
        self.set_model()
        self.pixel_spills = []
        self.falling_parts = []
        self.pt_lbls = []
        self.change_scene(self.Scene.MAIN_MENU)

    def trigger_pts_lbl(self, txt, x, y):
        self.pt_lbls.append(FadingPoints(txt, x, y))

    def trigger_falling_parts(self, src_x, src_y, colours=(255, 255, 255, 255), span=10):
        num_of = 80
        for x in np.linspace(src_x - span / 2, src_x + span / 2, num_of):
            offset = random.randint(-10, 10)
            self.falling_parts.append(FallingBlock(x + offset, src_y, 30, colours, 10))

    def trigger_pixel_spill(self, src_x, src_y, colours, circ_range_ratio, speed_ratio):
        start = 0
        for theta in np.linspace(start, start + circ_range_ratio * 2 * math.pi, num=15):
            ran_x = random.randint(0, 15)
            ran_y = random.randint(0, 15)
            self.pixel_spills.append(PixelSpillBlock(src_x + ran_x, src_y + ran_y, theta,
                                                     colours[random.randint(0, len(colours) - 1)],
                                                     speed=speed_ratio, size=1))

    def get_btn_labels(self):
        return "START_GAME", "OPTIONS", "EXIT"

    def set_font(self):
        pyglet.font.add_file('res/8-BIT WONDER.ttf')
        self.font_name = '8Bit Wonder'
        pyglet.font.load(self.font_name)

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

    def reset_flame_colours(self):
        self.flame_colours = []
        variation_blue = 100
        for i in range(0, 2):
            blue_val_1 = 255 - random.randint(0, variation_blue)
            blue_val_2 = 255 - random.randint(0, variation_blue)
            self.flame_colours.append(tuple([255, 255, 255, 255,
                                             0, 0, blue_val_1, 50,
                                             0, 0, blue_val_2, 50,
                                             255, 255, 255, 255]))

    def draw_game_screen(self):
        self.tick += 1
        if self.scene in (self.Scene.PLAYING, self.Scene.GAME_OVER, self.Scene.PAUSED):
            self.clear()
            self.draw_stars()
            self.draw_lasers()
            if self.scene == self.Scene.PLAYING or self.scene == self.Scene.PAUSED:
                self.draw_sprite_objs()
            self.draw_pixel_spills()
            self.draw_falling_parts()
            self.draw_point_lbls()
            self.draw_header()
            if self.scene == self.Scene.GAME_OVER:
                lines = ["It's Game Over", "R to Exit.", "Space to retry"]
                self.draw_display_txt(lines, 3 * [self.small_txt_size])
            elif self.scene == self.Scene.PAUSED:
                self.draw_pause_menu()
            if GameFrame.dev_mode:
                self.fps_display.draw()
        elif self.scene == self.Scene.MAIN_TO_PLAYING:
            self.clear()
            self.draw_stars()
            self.draw_header()
            self.draw_main_btns()
        elif self.scene == self.Scene.NEXT_LEVEL or self.scene == self.Scene.RESTART:
            self.clear()
            self.draw_stars()
            self.draw_header()
            self.draw_pixel_spills()
            self.draw_falling_parts()
            self.draw_point_lbls()

            lines = ["NEXT LEVEL IN" if self.scene == self.Scene.NEXT_LEVEL else "RESTART IN",
                     str((self.cooldown // (math.ceil(self.COOLDOWN // 3))) + 1)]
            self.draw_display_txt(lines, [self.large_txt_size, self.large_txt_size])

    def draw_stars(self):
        star_batch = Batch()
        for i in self.star_pts:
            star_batch.add(4, GL_QUADS, None, ('v2f', i))
        star_batch.draw()

    def draw_main_menu_background(self):
        self.draw_stars()

    def draw_sprite_objs(self):
        sprite_batch = Batch()
        self.rendered_sprite = []
        ship = self.model.player
        if ship.is_active:
            colour = self.player_glow_colour
            if self.model.player.is_blown:
                colour = [255, 0, 0]

            elif self.model.q_jam or self.model.e_jam:
                colour = [255, 0, 255]
            self.draw_illumination(self.to_screen_x(ship.x + ship.width // 2),
                                   self.to_screen_y(ship.y), 150 + self.player_glow_intensity,
                                   colour)
            player_batch = Batch()
            player_sprite = self.get_rendered_sprite(ship, player_batch)
            self.rendered_sprite.append(player_sprite)
            self.draw_flame(self.to_screen_x(ship.x), self.to_screen_y(ship.y), self.to_screen_x(ship.width))
            player_batch.draw()
        objs = []
        objs.extend(self.model.objects)
        if hasattr(self.model, 'boxes'):
            objs.extend(self.model.boxes)
        for obj in objs:
            if obj.is_active:
                sprite = self.get_rendered_sprite(obj, sprite_batch)
                self.rendered_sprite.append(sprite)

        sprite_batch.draw()

    def draw_display_txt(self, lines, font_sizes):
        y_padding = self.main_width // 35
        origin_y = 0.6 * self.height
        y_add = 0
        txt_batch = Batch()
        for i, line in enumerate(lines):
            lbl = pyglet.text.Label(
                line,
                batch=txt_batch,
                font_name='8Bit Wonder',
                font_size=font_sizes[i],
                width=self.main_width // 4, height=self.header_height * 2,
                x=self.main_width // 2, y=origin_y - y_add,
                anchor_x='center', anchor_y='center',
                color=(255, 255, 255, 255))
            y_add += font_sizes[i] + y_padding
        txt_batch.draw()

    def get_rendered_sprite(self, obj: GameObject, sprite_batch: Batch):
        if obj.img_name not in self.img_base.keys():
            self.render_sprite(obj)
        sprite = pyglet.sprite.Sprite(img=self.img_base[obj.img_name], batch=sprite_batch)
        sprite.x = self.main_width * (obj.x / self.model.MODEL_WIDTH)
        sprite.y = self.main_height * (obj.y / self.model.MODEL_HEIGHT)

        tgt_x = obj.width / self.model.MODEL_WIDTH
        tgt_y = obj.height / self.model.MODEL_HEIGHT
        sprite.scale_x = tgt_x * self.main_width / sprite.width
        sprite.scale_y = tgt_y * self.height / sprite.height
        return sprite

    def render_sprites(self):
        for obj in self.Sprites.get_sprite_names():
            self.render_sprite(obj)

    def render_sprite(self, obj):
        img_path = "img/" + obj.img_name
        stream = open(img_path, 'rb')
        self.img_base[obj.img_name] = pyglet.image.load(img_path, file=stream)

    def draw_point_lbls(self):
        pts: FadingPoints
        font_size = self.main_width // 140
        pts_batch = Batch()
        for pts in self.pt_lbls:
            pts.update()
            if pts.is_vanished:
                self.pt_lbls.remove(pts)
            else:
                pts_lbl = pyglet.text.Label(pts.txt,
                                            font_name='8Bit Wonder',
                                            font_size=font_size,
                                            width=self.main_width // 10, height=self.header_height // 2,
                                            x=pts.x, y=pts.y,
                                            anchor_x='left', anchor_y='top',
                                            color=(255, 255, 255, pts.alpha),
                                            batch=pts_batch)
        pts_batch.draw()

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

    def draw_falling_parts(self):
        pxl_batch = Batch()
        for bl in self.falling_parts:
            bl.update(self.tick)
        self.falling_parts[:] = [val for val in self.falling_parts if not val.is_vanished]
        num_of = 0
        px_vertices = []
        colours = []
        px: FallingBlock
        for px in self.falling_parts:
            num_of += 4
            px_vertices.extend((px.x, px.y, px.x, px.y + px.size,
                                px.x + px.size, px.y + px.size, px.x + px.size, px.y))
            colours.extend(px.colour)
        pxl_batch.add(num_of, GL_QUADS, None, ('v2f', px_vertices), ('c3B', colours))
        pxl_batch.draw()

    def draw_flame(self, x, y, width):
        flame_height = (self.main_height + self.main_width) // 90
        rocket_width = 8 * width // 64
        flame_width_reduct = 0
        offset = 15 * width // 64
        padding = 29 * width // 65

        if random.random() < 0.2:
            self.reset_flame_colours()

        flame_batch = Batch()
        srcs = [[x + offset + i * padding, x + offset + rocket_width + i * padding] for i in range(0, 2)]
        for i, [src_x1, src_x2] in enumerate(srcs):
            flame_batch.add(4, GL_QUADS, None,
                            ('v2f', [src_x1, y, src_x1 + flame_width_reduct, y - flame_height,
                                     src_x2 - flame_width_reduct, y - flame_height, src_x2, y]),
                            ('c4B', self.flame_colours[i]))
        flame_batch.draw()

    def draw_lasers(self):
        batch = Batch()
        inner_colors = (0, 200, 255, 0, 200, 255)
        radius = 3 * SpaceWindow.BULLET_RADIUS_PERCENT * self.width
        for bullet in self.model.bullets:
            # self.draw_illumination(self.to_screen_x(bullet[0]), self.to_screen_y(bullet[1]), radius, inner_colors[:3])
            batch.add(2, GL_LINES, None,
                      ('v2f', [self.to_screen_x(bullet[0]),
                               self.to_screen_y(bullet[1]),
                               self.to_screen_x(bullet[0]),
                               self.to_screen_y(bullet[1] + int(self.BULLET_HEIGHT_PERCENT * self.main_height))]),
                      ('c3B', inner_colors))
        radius = SpaceWindow.BULLET_RADIUS_PERCENT * self.width
        purple = [255, 0, 255]
        for x, y in self.model.alien_bullets:
            self.draw_illumination(self.to_screen_x(x), self.to_screen_y(y), 6 * radius, purple)
            circ_pts = [self.to_screen_x(x), self.to_screen_y(y) + radius]
            for theta in np.linspace(0, 2 * math.pi, 8):
                error = random.randint(-1 * radius // 4, radius // 4)
                circ_pts.extend([circ_pts[0] + (radius + error) * math.sin(theta),
                                 circ_pts[1] + (radius + error) * math.cos(theta)])
            num_of_vert = (len(circ_pts) // 2)
            colors = [255, 255, 255]
            colors.extend((num_of_vert - 1) * purple)
            graphics.draw(num_of_vert, GL_TRIANGLE_FAN,
                          ('v2f', circ_pts),
                          ('c3B', colors))
        batch.draw()

    def draw_illumination(self, x, y, radius, colors):
        circ_pts = [x, y + self.height * self.BULLET_HEIGHT_PERCENT // 2]
        for theta in np.linspace(0, 2 * math.pi, 10):
            error = 0
            circ_pts.extend([circ_pts[0] + (radius + error) * math.sin(theta),
                             circ_pts[1] + (radius + error) * math.cos(theta)])
        num_of_vert = (len(circ_pts) // 2)
        snip = list(colors)
        outer_colors = snip.copy()
        outer_colors.append(80)
        snip.append(0)
        outer_colors.extend((num_of_vert - 1) * snip)
        graphics.draw(num_of_vert, GL_TRIANGLE_FAN, ('v2f', circ_pts), ('c4B', outer_colors))

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
        self.enemies_lbl = pyglet.text.Label("Enemies Remaining: " + ("" if not self.model else str(self.model.aliens)),
                                             font_name='8Bit Wonder',
                                             font_size=self.main_width // 65,
                                             width=self.main_width, height=self.header_height,
                                             x=self.main_width // 40, y=self.main_height + 0.9 * self.header_height,
                                             anchor_x='left', anchor_y='top',
                                             color=(255, 255, 255, complement))
        self.enemies_lbl.draw()
        self.score_lbl = pyglet.text.Label("Score: " + ("" if not self.model else str(self.model.points)),
                                           font_name='8Bit Wonder',
                                           font_size=self.main_width // 65,
                                           width=self.main_width, height=self.header_height,
                                           x=18 * self.main_width // 40, y=self.main_height + 0.9 * self.header_height,
                                           anchor_x='left', anchor_y='top',
                                           color=(255, 255, 255, complement))
        self.score_lbl.draw()
        self.high_score_lbl = pyglet.text.Label("Highscore: " + ("" if not self.model else str(self.model.highscore)),
                                                font_name='8Bit Wonder',
                                                font_size=self.main_width // 65,
                                                width=self.main_width, height=self.header_height,
                                                x=28 * self.main_width // 40,
                                                y=self.main_height + 0.9 * self.header_height,
                                                anchor_x='left', anchor_y='top',
                                                color=(255, 255, 255, complement))
        self.high_score_lbl.draw()

    def play_main_menu_music(self):
        if self.main_menu_song is None:
            self.main_menu_song = self.play_sound("space_clones.mp3")

    def get_options(self):
        return {"CONTROLS": ["DEFAULT", ], "SOUND": {"ON", "OFF"}}

    def get_pause_options(self):
        return ["CONTINUE", "RETRY", "EXIT"]

    def clear_pts_and_restart(self):
        self.model.points = 0
        self.change_scene(self.Scene.RESTART)


class AnimatedObject(ABC):
    def __init__(self, x, y, vect=(0, 0), colour=None):
        self.x = x
        self.y = y
        self.vect = vect
        self.is_vanished = False
        self.colour = colour

    @abstractmethod
    def update(self):
        pass


class PixelSpillBlock(AnimatedObject):
    DEF_COLOUR = (255, 255, 255)
    BLOOD_COLOUR = (102, 0, 0)
    FLAME_COLOURS = [(255, 91, 20),
                     (255, 35, 35),
                     (255, 162, 85)]
    MAX_SPEED = 2
    SIZE_DECAY: float = 0.2
    TICK_RATE = 1
    DEF_SIZE = 8

    def __init__(self, x, y, vect, colour=None, speed=1, size=1):
        super().__init__(x, y, vect, (self.DEF_COLOUR if colour is None else colour))
        self.speed = self.MAX_SPEED * speed
        self.size = self.DEF_SIZE
        self.dx = 1
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


class FadingPoints(AnimatedObject):
    FADE_DECAY = 0.95

    def __init__(self, txt, x, y, colour=None):
        super().__init__(x, y, [0, 0], colour)
        self.alpha = 255
        self.txt = txt

    def update(self):
        if self.alpha <= 20:
            self.is_vanished = True
        else:
            self.alpha = int(self.alpha * self.FADE_DECAY)


class FallingBlock(AnimatedObject):
    DEF_COLOUR = (255, 255, 255)
    BLOOD_COLOUR = (102, 0, 0)
    FLAME_COLOURS = [(255, 91, 20),
                     (255, 35, 35),
                     (255, 162, 85)]
    MAX_SPEED = 3
    SIZE_DECAY: float = 0.2
    TICK_RATE = 2
    DEF_SIZE = 8
    GRAVITY_CONST = 1

    def __init__(self, x, y, upward_speed, colour=None, size=20):
        v = [random.randint(-upward_speed // 8, upward_speed // 8), random.random() * upward_speed]
        super().__init__(x, y, v, (self.DEF_COLOUR if colour is None else colour))
        self.size = size
        self.is_vanished = False

    def update(self, dt):
        if dt % self.TICK_RATE != 0:
            return
        if self.y < 0:
            self.is_vanished = True
        self.y += self.vect[1]
        self.vect[1] -= self.GRAVITY_CONST
        self.x += self.vect[0]


if __name__ == '__main__':
    window = SpaceWindow(True if len(sys.argv) > 1 and str(sys.argv[1]).lower() == "true" else False)
    delta = 1.0 / 60
    pyglet.clock.schedule_interval(window.update, delta)
    pyglet.app.run()
