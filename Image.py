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


class Sprite(pygame.sprite.Sprite):
    def __init__(self, screen, img_name, x, y, tweak_x=0, tweak_y=0):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen

        # 画像の読み込み
        self.name = img_name  # スプライトの名前
        self.image = LoadImage.image_list[img_name]

        # 画面内の座標
        self.x = x * 29 + tweak_x
        self.y = y * 29 - 12 + tweak_y

        # スプライトのサイズ
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # 初期位置に描画
        self.rect = Rect(int(self.x), int(self.y), self.width, self.height)
        screen.blit(self.image, self.rect)

    def update(self):
        # 画面スクロール
        if self.rect.left > -150:
            self.rect.left -= SpritePlayer.scroll
            # 画面内の領域のみ描画
            if self.rect.left < 480:
                self.screen.blit(self.image, self.rect)


class SpriteEnemy(Sprite):
    def __init__(self, screen, img_name, x, y, tweak_x=0, tweak_y=0):
        super().__init__(screen, img_name, x, y, tweak_x, tweak_y)

        # 画像を格納
        self.img_left = self._load_image()
        self.img_right = [pygame.transform.flip(img, True, False) for img in self.img_left]

        self.x_speed = 0.5  # 移動速度
        self.y_speed = 0.0  # 落下速度
        self.direction = 1  # 向き （1 or -1）

    def update(self, list_number=0):
        # 画面スクロール
        if self.rect.left > -150:
            self.rect.left -= SpritePlayer.scroll

            # 画面内の領域のみ描画
            if self.rect.left < 550:
                self.rect.left = round(self.x) - SpritePlayer.scroll_sum
                self.rect.top = round(self.y)

                # 向きによって画像を変更
                if self.direction == 1:
                    self.screen.blit(self.img_left[list_number], self.rect)
                else:
                    self.screen.blit(self.img_right[list_number], self.rect)

    # 画像の読み込み
    def _load_image(self):
        img = [self.image]

        # 画像が複数ある場合はリストに追加
        if "1" in self.name:
            for i in range(1, 5):
                name = self.name[:-1] + str(i)
                if name in LoadImage.image_list:
                    img.append(LoadImage.image_list[name])
        return img


class SpritePlayer(pygame.sprite.Sprite):
    scroll = 0  # 1フレームの画面スクロール値
    scroll_sum = 0  # 画面スクロール量の合計

    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)

        self.screen = screen

        # 画像の格納
        img = LoadImage.image_list
        self.image = img['player1']
        self.img_right = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5']]
        self.img_left = [pygame.transform.flip(img, True, False) for img in self.img_right]

        self.x_speed = self.y_speed = 0.0  # 速度
        self.max_speed = 0  # x方向の最大速度 （変数）
        self.AIR_MAX_SPEED = 0  # 空中加速時の最大速度
        self.JUMP_SPEED = 0  # ジャンプ速度

        self.isGrounding = True  # 地面に着地しているか
        self.isJump = False  # ジャンプモーション中か
        self.isDeath = False  # 敵に当たったかどうか

        # 初期座標セット
        self.x = 80
        self.y = 320
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = Rect(self.x, self.y, self.width, self.height)

    def update(self, image):
        SpritePlayer.scroll = self.scroll
        SpritePlayer.scroll_sum = self.scroll_sum

        self.rect.left = int(self.x)
        self.rect.top = int(self.y)
        self.screen.blit(image, self.rect)

    # 空中時の最大速度を計算
    def limit_air_speed(self):
        if abs(self.x_speed) < self.AIR_MAX_SPEED:
            self.max_speed = self.AIR_MAX_SPEED
        else:
            self.max_speed = abs(self.x_speed)
