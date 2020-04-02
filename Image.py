import pygame
import pathlib
import os
from pygame.locals import *


class LoadImage:
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
