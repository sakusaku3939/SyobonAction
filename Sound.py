import pygame
import pathlib
import os

pygame.mixer.init(channels=1, buffer=128)


class Sound:
    SE_list = {}  # 効果音を格納するリスト

    @classmethod
    def __init__(cls):
        file_list = pathlib.Path(f'SE/').glob('*.wav')

        for file in file_list:
            name = os.path.splitext(file.name)[0]
            data = pygame.mixer.Sound(f"SE/{file.name}")

            cls.SE_list[name] = data

    @classmethod
    def play_BGM(cls, name):
        pygame.mixer.music.load(f'BGM/{name}.mp3')
        pygame.mixer.music.play(-1)

    @classmethod
    def stop_BGM(cls):
        pygame.mixer.music.stop()

    @classmethod
    def play_SE(cls, name):
        cls.SE_list[name].play()

    @classmethod
    def stop_SE(cls, name=''):
        if name == '':
            [cls.SE_list[_name].stop() for _name in cls.SE_list]
        else:
            cls.SE_list[name].stop()
