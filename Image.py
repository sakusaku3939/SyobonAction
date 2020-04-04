import pygame
import pathlib
import os
from pygame.locals import *


class LoadImage:
    # 画像データを格納するリスト
    image_list = None

    def __init__(self):
        self.image_list = {'title': pygame.image.load("res/title.png").convert()}
        folder_list = ['player', 'enemy', 'bg', 'item', 'block']

        # 画像データを読み込む
        for folder in folder_list:
            file_list = pathlib.Path(f'res/{folder}/').glob('*.png')

            for file in file_list:
                image_name = os.path.splitext(file.name)[0]
                image = pygame.image.load(f"res/{folder}/{file.name}").convert()
                self.image_list[image_name] = image

        # 画像の透過
        for image in self.image_list.values():
            image.set_colorkey((153, 255, 255), RLEACCEL)

        LoadImage.image_list = self.image_list


class Sprite(pygame.sprite.Sprite):
    def __init__(self, screen, img_name, x, y, tweak_x=0, tweak_y=0):
        self.screen = screen
        self.name = img_name

        pygame.sprite.Sprite.__init__(self)

        self.image = LoadImage.image_list[img_name]
        width = self.image.get_width()
        height = self.image.get_height()
        self.x = x * 29 + tweak_x
        self.y = y * 29 - 12 + tweak_y
        self.rect = Rect(self.x, self.y, width, height)

        screen.blit(self.image, self.rect)

    # 画面スクロール
    def update(self, scroll):
        # 画面内の領域のみ描画
        if self.rect.left > -150:
            self.rect.left -= scroll
            if self.rect.left < 480:
                self.screen.blit(self.image, self.rect)
