import pygame
import random
import numpy as np


class Text:
    text_list = []

    class __DrawText:
        def __init__(self, screen, sprite, text, x, y, tweak_x, tweak_y, size):
            self.screen = screen
            self.sprite = sprite
            self.text = text
            self.x = x
            self.y = y
            self.tweak_x = tweak_x
            self.tweak_y = tweak_y
            self.size = size

            self.time = 120

        def draw(self):
            if self.sprite is not None:
                self.x = self.sprite.rect.right + self.tweak_x
                self.y = self.sprite.rect.top + self.tweak_y

                if self.x < -20:
                    return True

            # 文字のアウトライン
            for tweak in range(2):
                font = pygame.font.SysFont("msgothicmsuigothicmspgothic", self.size)
                text_data = font.render(self.text, True, (0, 0, 0))
                for i in range(4):
                    rad = i / 2 * np.pi
                    x = np.cos(rad) + self.x
                    y = np.sin(rad) + self.y
                    self.screen.blit(text_data, [x + tweak, y])

            # 文字本体
            for tweak in range(2):
                font = pygame.font.SysFont("msgothicmsuigothicmspgothic", self.size)
                text_data = font.render(self.text, True, (255, 255, 255))
                self.screen.blit(text_data, [self.x + tweak, self.y])

            return False

    @classmethod
    def set(cls, screen, text, x=0, y=0, size=20, sprite=None, tweak_x=0, tweak_y=0):
        if type(text) is str:
            cls.text_list.append(cls.__DrawText(screen, sprite, text, x, y, tweak_x, tweak_y, size))

        elif type(text) is list:
            index = random.randint(0, len(text) - 1)
            cls.text_list.append(cls.__DrawText(screen, sprite, text[index], x, y, tweak_x, tweak_y, size))

    @classmethod
    def update(cls):
        isRemove = False
        for count, text in enumerate(cls.text_list):
            if count < 3:
                isRemove = text.draw()

            text.time -= 1
            if text.time == 0 or isRemove:
                cls.text_list.remove(text)
