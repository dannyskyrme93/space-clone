from pyglet.window import key, Window, mouse
from abc import ABCMeta, abstractmethod
from enum import Enum

import math
import pyglet
import sys
from pyglet import graphics
from pyglet.graphics import Batch, GL_QUADS
from model import GameModel, GameEvent, GameObject
from functools import partial

KEY_PRESS, KEY_RELEASE = 0, 1


class GameFrame(Window):
    __metaclass__ = ABCMeta

    class Scene(Enum):
        PLAYING = 0
        MAIN_MENU = 1
        CLOSING = 2

    class KeyAction(Enum):
        KEY_PRESS, KEY_RELEASE = 0, 1

    MENU = ["START", "PREFERENCES", "QUIT"]
    MAIN_BTN_WIDTH_PERCENT, MAIN_BTN_HEIGHT_PERCENT, MAIN_BTN_LBLS_PADDING_Y_PERCENT = 0.25, 0.1, 0.1
    COOLDOWN = 0

    main_scenes = [Scene.PLAYING,
                   Scene.MAIN_MENU,
                   Scene.CLOSING]

    main_width: int = 1700
    main_height: int = 800
    header_height: int = 50

    def __init__(self, dev_mode=False):
        self.model = None
        self.to_clear = False
        self.dev_mode = dev_mode
        super(GameFrame, self).__init__(self.main_width, self.main_height + self.header_height, visible=False)
        self.main_menu_song = None
        icon = pyglet.image.load('img/x-wing_icon.png')
        self.set_icon(icon)
        self.set_btns()
        self.scene = None
        self.max_cooldown = 0
        self.cooldown = self.max_cooldown
        if not self.dev_mode:
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
        self.set_visible(True)

    def on_key_press(self, symbol, modifiers):
        if self.model:
            self.model.action(symbol, KEY_PRESS)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.close()
        elif self.scene != self.Scene.MAIN_MENU:
            self.model.action(symbol, KEY_RELEASE)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT and self.scene == self.Scene.MAIN_MENU:
            self.menu_mouse_action(x, y)

    def on_draw(self):
        if self.scene == self.Scene.MAIN_MENU:
            self.clear()
            self.draw_main_menu_background()
            self.draw_main_btns()
        else:
            self.draw_game_screen()

    def menu_mouse_action(self, x, y):
        if self.scene == self.Scene.MAIN_MENU:
            for btn in self.main_btns:
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

    @abstractmethod
    def change_scene(self, scene):
        pass

    @abstractmethod
    def reset(self):
        self.model: GameModel = GameModel

    @abstractmethod
    def draw_main_menu_background(self):
        pass

    @abstractmethod
    def set_btns(self):
        btn_width, btn_height = self.width * GameFrame.MAIN_BTN_WIDTH_PERCENT, \
                                self.height * GameFrame.MAIN_BTN_HEIGHT_PERCENT
        self.main_btns = [
            GameButton(self.get_btn_labels()[y], self.width // 2, 0.8 * self.height - (y + 1) * btn_height -
                       y * self.height * GameFrame.MAIN_BTN_LBLS_PADDING_Y_PERCENT, btn_width, btn_height,
                       partial(self.change_scene, self.main_scenes[y]))
            for y in range(0, len(GameFrame.MENU))]

    @abstractmethod
    def get_btn_labels(self):
        return GameFrame.MENU

    @abstractmethod
    def set_model(self):
        pass

    def to_screen_x(self, mod_x):
        return self.main_width * mod_x // self.model.MODEL_WIDTH

    def to_screen_y(self, mod_y):
        return self.main_height * mod_y // self.model.MODEL_HEIGHT

    @abstractmethod
    def play_main_menu_music(self):
        pass

    @abstractmethod
    def play_sound(self, ev: GameEvent):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def draw_game_screen(self):
        pass

    @abstractmethod
    def draw_game_over_screen(self):
        pass


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

# if __name__ == '__main__':
#     print("System arguments:", sys.argv)
#     window = GameFrame(True if len(sys.argv) > 1 and str(sys.argv[1]).lower() == "true" else False)
#     pyglet.clock.set_fps_limit(60)
#     delta = 1.0 / 60
#     pyglet.clock.schedule_interval(window.update, delta)
#     pyglet.app.run()
