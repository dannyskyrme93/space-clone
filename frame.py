from pyglet.window import key, Window, mouse
from enum import Enum

import math
import pyglet
import sys
from pyglet import graphics
from pyglet.graphics import Batch, GL_QUADS, GL_LINES
from model import GameModel, GameEvent, GameObject
from functools import partial

KEY_PRESS, KEY_RELEASE = 0, 1


class GameFrame(Window):
    class Scene(Enum):
        PLAYING = 0
        MAIN_MENU = 1
        CLOSING = 2
        MAIN_MENU_WITH_OPTIONS = 3

    class KeyAction(Enum):
        KEY_PRESS, KEY_RELEASE = 0, 1

    MENU = ["START", "PREFERENCES", "QUIT"]
    MAIN_BTN_WIDTH_PERCENT, MAIN_BTN_HEIGHT_PERCENT, MAIN_BTN_LBLS_PADDING_Y_PERCENT = 0.25, 0.1, 0.1
    COOLDOWN = 0
    OPT_ORIGIN_X_PERCENT, OPT_ORIGIN_Y_PERCENT = 0.25, 0.25
    main_scenes = [Scene.PLAYING,
                   Scene.MAIN_MENU,
                   Scene.CLOSING]

    main_width: int = 1700
    main_height: int = 800
    header_height: int = 50

    def __init__(self, dev_mode=False):
        self.model = None
        self.to_clear = False
        GameFrame.dev_mode = dev_mode
        super(GameFrame, self).__init__(self.main_width, self.main_height + self.header_height, visible=False)
        self.main_menu_song = None
        icon = pyglet.image.load('img/x-wing_icon.png')
        self.set_icon(icon)
        self.set_btns()
        self.scene = None
        self.max_cooldown = 0
        self.cooldown = self.max_cooldown
        if not GameFrame.dev_mode:
            self.change_scene(self.Scene.MAIN_MENU)
            self.sound_player = pyglet.media.Player()
            self.set_fullscreen(True)
            self.main_width = self.width
            ratio = self.header_height / self.main_height
            self.header_height = math.floor(self.height * ratio)
            self.main_height = math.floor(self.height * (1 - ratio))
            self.sound_base = {}
            self.play_main_menu_music()
        else:
            self.set_model()
            self.change_scene(self.Scene.PLAYING)
            self.fps_display = pyglet.clock.ClockDisplay()
            self.set_location(220, 30)
            self.width = self.main_width
            self.height = self.main_height + self.header_height
        self.set_font()
        self.set_visible(True)
        self.set_btns()

    def on_key_press(self, symbol, modifiers):
        if self.model:
            self.model.action(symbol, KEY_PRESS)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            sys.exit()
        elif self.scene not in {self.Scene.MAIN_MENU, self.Scene.MAIN_MENU_WITH_OPTIONS}:
            self.model.action(symbol, KEY_RELEASE)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT and self.scene in {self.Scene.MAIN_MENU, self.Scene.MAIN_MENU_WITH_OPTIONS}:
            self.menu_mouse_action(x, y)

    def on_draw(self):
        if self.scene in {self.Scene.MAIN_MENU, self.Scene.MAIN_MENU_WITH_OPTIONS}:
            self.clear()
            self.draw_main_menu_background()
            self.draw_main_btns()
            if self.scene == self.Scene.MAIN_MENU_WITH_OPTIONS:
                self.draw_options_panel()
        else:
            self.draw_game_screen()

    def menu_mouse_action(self, x, y):
        if self.scene == self.Scene.MAIN_MENU:
            for btn in self.main_btns:
                if btn.is_on(x, y):
                    print(btn.lbl)
                    btn.click()
        elif self.scene == self.Scene.MAIN_MENU_WITH_OPTIONS:
            # TODO this is temp
            for btn in self.opt_btns:
                if btn.is_on(x, y):
                    print(btn.lbl)
                    btn.click()

    def draw_main_btns(self):
        for btn in self.main_btns:
            graphics.draw(4, GL_QUADS, ['v2f', [btn.x - btn.width // 2, btn.y - btn.height // 2,
                                                btn.x - btn.width // 2, btn.y + btn.height // 2,
                                                btn.x + btn.width // 2, btn.y + btn.height // 2,
                                                btn.x + btn.width // 2, btn.y - btn.height // 2]],
                          ['c4B', tuple(btn.color)])
            btn_lbl = pyglet.text.Label(btn.lbl,
                                        font_name='8Bit Wonder',
                                        font_size=0.3 * btn.height,
                                        width=btn.width, height=0.5 * btn.height,
                                        x=btn.x, y=btn.y,
                                        anchor_x='center', anchor_y='center',
                                        color=(255, 255, 255, btn.get_alpha()))
            btn_lbl.draw()

    def draw_options_panel(self):
        origin_x = self.OPT_ORIGIN_X_PERCENT * self.width
        origin_y = self.OPT_ORIGIN_Y_PERCENT * self.height
        panel_width = 2 * (0.5 - self.OPT_ORIGIN_X_PERCENT) * self.width
        panel_height = 2 * (0.5 - self.OPT_ORIGIN_Y_PERCENT) * self.height
        graphics.draw(4, GL_QUADS, ['v2f', [origin_x, origin_y,
                                            origin_x, origin_y + panel_height,
                                            origin_x + panel_width, origin_y + panel_height,
                                            origin_x + panel_width, origin_y]],
                      ['c4B', tuple(GameButton.DEF_COLOR)])
        for btn in self.opt_btns:
            graphics.draw(4, GL_QUADS, ['v2f', [btn.x - btn.width // 2, btn.y - btn.height // 2,
                                                btn.x - btn.width // 2, btn.y + btn.height // 2,
                                                btn.x + btn.width // 2, btn.y + btn.height // 2,
                                                btn.x + btn.width // 2, btn.y - btn.height // 2]],
                          ['c4B', tuple(btn.color)])
            if btn.outlined:
                graphics.draw(8, GL_LINES, ['v2f', [btn.x - btn.width // 2, btn.y - btn.height // 2,
                                                    btn.x - btn.width // 2, btn.y + btn.height // 2,

                                                    btn.x - btn.width // 2, btn.y + btn.height // 2,
                                                    btn.x + btn.width // 2, btn.y + btn.height // 2,

                                                    btn.x + btn.width // 2, btn.y + btn.height // 2,
                                                    btn.x + btn.width // 2, btn.y - btn.height // 2,

                                                    btn.x + btn.width // 2, btn.y - btn.height // 2,
                                                    btn.x - btn.width // 2, btn.y - btn.height // 2]])

            btn_lbl = pyglet.text.Label(btn.lbl,
                                        font_name='8Bit Wonder',
                                        font_size=0.3 * btn.height,
                                        width=btn.width, height=0.5 * btn.height,
                                        x=btn.x, y=btn.y,
                                        anchor_x='center', anchor_y='center',
                                        color=(255, 255, 255, btn.get_alpha()))
            btn_lbl.draw()

    def set_btns(self):
        btn_width, btn_height = self.width * GameFrame.MAIN_BTN_WIDTH_PERCENT, \
                                self.height * GameFrame.MAIN_BTN_HEIGHT_PERCENT
        main_lbls = self.get_btn_labels()
        self.main_btns = [
            GameButton(main_lbls[y], self.width // 2, 0.8 * self.height - (y + 1) * btn_height -
                       y * self.height * GameFrame.MAIN_BTN_LBLS_PADDING_Y_PERCENT, btn_width, btn_height,
                       partial(self.change_scene, self.main_scenes[y]))
            for y in range(0, len(GameFrame.MENU))]

        self.opt_btns = []
        opt_contents = self.get_options()
        dark = [c - 80 for c in GameButton.DEF_COLOR]
        darker = [c - 40 for c in GameButton.DEF_COLOR]

        origin_x = (self.OPT_ORIGIN_X_PERCENT + 0.025) * self.width
        origin_y = (self.OPT_ORIGIN_Y_PERCENT + 0.025) * self.height
        panel_width = 2 * (0.5 - self.OPT_ORIGIN_X_PERCENT) * self.width
        panel_height = 2 * (0.5 - self.OPT_ORIGIN_Y_PERCENT) * self.height

        opt_btn_width = btn_width // 2
        opt_btn_height = btn_height // 2
        padding_x = opt_btn_width // 4
        padding_y = opt_btn_height // 4
        for i, k in enumerate(opt_contents):
            opt = k
            choices = opt_contents[k]
            print(i, opt, choices)
            y = 0.9 * (origin_y + panel_height) - i * (padding_y + btn_height)

            btn = GameButton(opt, origin_x + opt_btn_width // 2, y, opt_btn_width, opt_btn_height,
                             partial(print, opt))
            btn.color = dark
            self.opt_btns.append(btn)
            for j, choice in enumerate(opt_contents[k]):
                btn = GameButton(choice, origin_x + opt_btn_width // 2 + (j + 1) * (opt_btn_width + padding_y),
                                 y, opt_btn_width,
                                 opt_btn_height,
                                 partial(print, opt))
                btn.color = darker
                btn.func = btn.toggle
                self.opt_btns.append(btn)
        close_size = opt_btn_height // 2
        options_close_btn = GameButton("", origin_x + panel_width - 2.5 * close_size,
                                       origin_y + panel_height - 1.75 * close_size,
                                       close_size, close_size, partial(self.change_scene,
                                                                       self.Scene.MAIN_MENU))
        options_close_btn.color = 4 * (179, 30, 60, 255)
        self.opt_btns.append(options_close_btn)

    def to_screen_x(self, mod_x):
        return self.main_width * mod_x // self.model.MODEL_WIDTH

    def to_screen_y(self, mod_y):
        return self.main_height * mod_y // self.model.MODEL_HEIGHT

    def set_font(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def get_btn_labels(self):
        raise NotImplementedError

    def change_scene(self, scene):
        raise NotImplementedError

    def draw_main_menu_background(self):
        raise NotImplementedError

    def get_options(self):
        return {"Choice 1": ["Something", "Some"], "Choice 2": {"Something2", "Yeh"}}

    def get_btn_labels(self):
        raise NotImplementedError

    def set_model(self):
        raise NotImplementedError

    def play_main_menu_music(self):
        raise NotImplementedError

    def play_sound(self, ev: GameEvent):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def draw_game_screen(self):
        raise NotImplementedError

    def get_font(self):
        raise NotImplementedError


class GameButton:
    DEF_COLOR = 4 * [125, 125, 125, 255]

    def __init__(self, lbl: str, x: float, y: float, width: float, height: float, func):
        self.lbl = lbl
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.func = func
        self.color = GameButton.DEF_COLOR
        self.outlined: bool = False

    def change_alpha(self, alpha):
        alpha = int(alpha)
        for i in range(3, len(self.color), 4):
            self.color[i] = alpha

    def get_alpha(self):
        return self.color[3]

    def is_on(self, x, y):
        if self.x - self.width // 2 <= x <= self.x + self.width // 2 \
                and self.y - self.height // 2 <= y <= self.y + self.height // 2:
            return True
        return False

    def click(self):
        self.func()

    def toggle(self):
        self.outlined = not self.outlined

# if __name__ == '__main__':
#     g = GameFrame()
#     g.update(1)
