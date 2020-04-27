import pygame
import pathlib
import os
from pygame.locals import *


class LoadImage:
    image_list = {}  # 画像データを格納するリスト

    def __init__(self):
        image_list = {'title': pygame.image.load("res/title.png").convert()}
        folder_list = ['player', 'enemy', 'bg', 'item', 'block']

        # 画像データを読み込む
        for folder in folder_list:
            file_list = pathlib.Path(f'res/{folder}/').glob('*.png')

            for file in file_list:
                name = os.path.splitext(file.name)[0]
                data = pygame.image.load(f"res/{folder}/{file.name}").convert()

                # 画像の透過
                if name == 'goal_pole':
                    data.set_colorkey((160, 180, 250), RLEACCEL)
                else:
                    data.set_colorkey((153, 255, 255), RLEACCEL)

                image_list[name] = data

        LoadImage.image_list = image_list
