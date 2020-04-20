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
    def __init__(self, screen, img_name, data, x, y, tweak_x=0, tweak_y=0):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen

        # スプライトのアニメーション
        self.isAnimation = False
        self.ani_x = self.ani_y = 0

        # 画像の番号
        self.data = data

        # 画像の読み込み
        self.name = img_name  # スプライトの名前
        self.image = LoadImage.image_list[img_name]

        # ステージ全体での座標
        self.x = int(x * 29 + tweak_x)
        self.y = int(y * 29 - 12 + tweak_y)

        """ # 画面内での座標
        self.rect.left = self.x - SpritePlayer.scroll_sum
        self.rect.top = self.y
        """

        # スプライトのサイズ
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # 初期位置に描画
        self.rect = Rect(self.x - SpritePlayer.initial_scroll_sum, self.y, self.width, self.height)
        screen.blit(self.image, self.rect)

        # 描画する範囲
        self.START_RANGE = -150
        self.END_RANGE = 480

        # トゲを生やすか
        self.isThorns = False
        self.thorns_img = LoadImage.image_list['block38']
        self.thorns_tweak_x = self.width / 2 - self.thorns_img.get_width() / 2 - 1
        self.thorns_tweak_y = self.height / 2 - self.thorns_img.get_height() / 2 - 1

        # 隠しブロック
        self.isHide = True if img_name == 'block3' else False

    def update(self):
        # 画面スクロール
        self.rect.left = self.x - SpritePlayer.scroll_sum

        # 画面内の領域のみ描画
        if self.START_RANGE < self.x - SpritePlayer.scroll_sum < self.END_RANGE:
            # トゲを生やす場合
            if self.isThorns:
                thorns_x = self.rect.left + self.thorns_tweak_x
                thorns_y = self.rect.top + self.thorns_tweak_y
                self.screen.blit(self.thorns_img, (thorns_x, thorns_y))

            if not self.isHide:
                self.screen.blit(self.image, self.rect)


class SpriteEnemy(Sprite):
    def __init__(self, screen, img_name, data, x, y, tweak_x=0, tweak_y=0):
        super().__init__(screen, img_name, data, x, y, tweak_x, tweak_y)

        # 画像を格納
        self.img_left = self._load_image()
        self.img_right = [pygame.transform.flip(img, True, False) for img in self.img_left]

        self.x_speed = 0.5  # 移動速度
        self.y_speed = 0.0  # 落下速度
        self.direction = 1  # 向き （1 or -1）

        # 描画する範囲
        self.START_RANGE = -100
        self.END_RANGE = 550
        self.isDraw = False
        self.isRemove = False

    def update(self, list_number=0):
        if self.x - SpritePlayer.scroll_sum < self.END_RANGE or self.isDraw:
            self.isDraw = True

            # 描画位置を計算
            self.rect.left = self.x - SpritePlayer.scroll_sum
            self.rect.top = self.y

            # 向きによって画像を変更
            if self.direction == 1:
                self.screen.blit(self.img_left[list_number], self.rect)
            else:
                self.screen.blit(self.img_right[list_number], self.rect)

            # 画面外になったらオブジェクト削除
            if self.x - SpritePlayer.scroll_sum < self.START_RANGE:
                self.isRemove = True

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
    # 初期座標
    initial_x = 80
    initial_y = 320
    initial_scroll_sum = 0

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
        self.x = SpritePlayer.initial_x
        self.y = SpritePlayer.initial_y
        SpritePlayer.scroll_sum = SpritePlayer.initial_scroll_sum
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = Rect(self.x, self.y, self.width, self.height)

    def update(self, image):
        self.rect.left = self.x
        self.rect.top = self.y
        self.screen.blit(image, self.rect)

    # 空中時の最大速度を計算
    def limit_air_speed(self):
        if abs(self.x_speed) < self.AIR_MAX_SPEED:
            self.max_speed = self.AIR_MAX_SPEED
        else:
            self.max_speed = abs(self.x_speed)
