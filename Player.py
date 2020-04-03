import pygame
from pygame.locals import *
import numpy as np

from Image import LoadImage


class Player(pygame.sprite.Sprite):
    # プレイヤー座標
    player_x = player_y = 0
    # 1フレームの画面スクロール値
    scroll = 0

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        img = LoadImage.image_list
        self.image = img['player1']
        self.img_right = [img['player1'], img['player2'], img['player3'], img['player4']]
        self.img_left = [pygame.transform.flip(i, True, False) for i in self.img_right]

        width = self.image.get_width()
        height = self.image.get_height()
        self.rect = Rect(60, 329, width, height)

        self.player_x = self.rect.left
        self.player_y = self.rect.top

        self.x_speed = self.y_speed = 0  # 速度
        self.ACCELERATION = 0.1  # 加速度
        self.DASH_ACCELERATION = 0.22  # ダッシュ時の加速度
        self.FRICTION_ACCELERATION = 0.13  # 地面摩擦時の加速度
        self.MAX_SPEED = 4  # 最大速度

        self.scroll_sum = 0  # 画面スクロール量の合計
        self.SCROLL_LIMIT = 3605  # 画面スクロール上限

        self.isGrounding = True  # 落下しているか
        self.FALL_ACCELERATION = 0.3  # 落下加速度

        self.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -7.4  # ジャンプ速度
        self.ADD_JUMP_SPEED = -2.1  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -1  # 追加のダッシュジャンプ速度
        self.jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか

    def update(self, screen):
        pressed_key = pygame.key.get_pressed()

        # 画像アニメーション
        img_number = int(self.player_x / 20) % 2
        animation = (lambda num: self.img_left[num] if self.isLeft else self.img_right[num])

        # ジャンプ
        if pressed_key[K_UP] and self.isGrounding:
            self.isJump = True
            self.y_speed = self.JUMP_SPEED

        # 8フレーム以内にキーを離した場合小ジャンプ
        if not pressed_key[K_UP]:
            self.isJump = False
            self.jump_time = 0
        elif self.isJump:
            # 8フレーム以上キー長押しで大ジャンプ
            if self.jump_time >= 8:
                self.y_speed += self.ADD_JUMP_SPEED
                self.isJump = False
                # 移動スピードが最大の時、更にジャンプの高さを追加
                if abs(self.x_speed) == self.MAX_SPEED:
                    self.y_speed += self.ADD_DASH_JUMP_SPEED
            else:
                self.jump_time += 1

        # 土管に入る
        if pressed_key[K_DOWN]:
            pass

        # 左移動
        if pressed_key[K_LEFT]:
            self.x_speed -= self.ACCELERATION if self.x_speed < -1 else self.DASH_ACCELERATION
            self.isLeft = True

        # 右移動
        elif pressed_key[K_RIGHT]:
            self.x_speed += self.ACCELERATION if self.x_speed > 1 else self.DASH_ACCELERATION
            self.isLeft = False

        # 地面摩擦
        elif self.isGrounding:
            self.x_speed -= self.FRICTION_ACCELERATION * np.sign(self.x_speed)

        # 最大速度
        self.x_speed = np.clip(self.x_speed, -self.MAX_SPEED, self.MAX_SPEED)

        # 画面外に出ないようにする
        if (self.player_x + self.x_speed < 0) and not (pressed_key[K_RIGHT] and self.x_speed >= 0):
            self.x_speed = 0
            self.player_x = 0
        if (self.player_x + self.x_speed > 450) and not (pressed_key[K_LEFT] and self.x_speed <= 0):
            self.x_speed = 0
            self.player_x = 450

        # 地面判定
        if self.player_y + self.y_speed < 330:
            self.isGrounding = False
            self.y_speed += self.FALL_ACCELERATION
            img_number = 2
        else:
            self.y_speed = 0
            self.player_y = 330
            self.isGrounding = True
            self.isJump = False

        # 座標を計算
        self.player_y += int(self.y_speed)
        self.player_x += int(self.x_speed)
        self.rect.left = self.player_x
        self.rect.top = self.player_y

        # 画面スクロール
        if self.player_x >= 210:
            # スクロール上限
            if self.scroll_sum < self.SCROLL_LIMIT:
                self.player_x = 210
                self.scroll = int(self.x_speed)
                self.scroll_sum += self.scroll
            else:
                self.scroll = 0

        # 描画
        screen.blit(animation(img_number), self.rect)

        return self.scroll
