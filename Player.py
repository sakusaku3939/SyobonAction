import pygame
from pygame.locals import *
import numpy as np

from Image import LoadImage


class Player(pygame.sprite.Sprite):
    # プレイヤー座標
    player_x = player_y = 0
    # 1フレームの画面スクロール値
    scroll = 0

    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)

        self.screen = screen

        img = LoadImage.image_list
        self.image = img['player1']
        self.img_right = [img['player1'], img['player2'], img['player3'], img['player4']]
        self.img_left = [pygame.transform.flip(i, True, False) for i in self.img_right]

        width = self.image.get_width()
        height = self.image.get_height()
        self.rect = Rect(80, 320, width, height)

        self.player_x = self.rect.left
        self.player_y = self.rect.top

        self.x_speed = self.y_speed = 0.0  # 速度
        self.ACCELERATION = 0.07  # 加速度
        self.DASH_ACCELERATION = 0.25  # 反転ダッシュ時の加速度
        self.FRICTION_ACCELERATION = 0.13  # 地面摩擦時の減速度
        self.MAX_SPEED_X = 4  # x方向の最大速度
        self.MAX_SPEED_Y = 8  # y方向の最大速度
        self.max_speed = 0  # 最大速度 （変数）

        self.SCROLL_LIMIT = 3605  # 画面スクロール上限
        self.scroll_sum = 0  # 画面スクロール量の合計

        self.isGrounding = True  # 落下しているか
        self.FALL_ACCELERATION = 0.3  # 落下加速度

        self.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -7.2  # ジャンプ速度
        self.ADD_JUMP_SPEED = -2.4  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -1.2  # 追加のダッシュジャンプ速度
        self.jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか
        self.isHIT_Head = False  # 頭がブロックに当たったか

        self.img_number = 0  # x座標が20変わるごとに画像を切り替え
        self.animation = None  # 向きに応じて画像を切り替え

        self.rect_size_x = 4  # x方向の当たり判定の大きさ
        self.rect_size_y = 6  # y方向の当たり判定の大きさ

    def update(self, stage):
        pressed_key = pygame.key.get_pressed()

        # 画像アニメーション
        self.img_number = int((self.player_x + self.scroll_sum) / 20) % 2
        self.animation = (lambda num: self.img_left[num] if self.isLeft else self.img_right[num])

        # ジャンプ
        jump_key = pressed_key[K_UP] or pressed_key[K_z]
        if jump_key and self.isGrounding:
            self.isJump = True
            self.jump_time = 0
            self.y_speed = self.JUMP_SPEED
            if abs(self.x_speed) < self.MAX_SPEED_X - 2:
                self.max_speed = self.MAX_SPEED_X - 1

        # 8フレーム以内にキーを離した場合小ジャンプ
        if not jump_key:
            self.isJump = False
            self.jump_time = 0
        elif self.isJump:
            # 8フレーム以上キー長押しで大ジャンプ
            if self.jump_time >= 8:
                self.y_speed += self.ADD_JUMP_SPEED
                self.isJump = False
                # 移動スピードが最大の時、更にジャンプの高さを追加
                if abs(self.x_speed) == self.MAX_SPEED_X:
                    self.y_speed += self.ADD_DASH_JUMP_SPEED
            else:
                self.jump_time += 1

        # 土管に入る
        elif pressed_key[K_DOWN]:
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
            if abs(self.x_speed) > 0.1:
                self.x_speed -= self.FRICTION_ACCELERATION * np.sign(self.x_speed)
            else:
                self.x_speed = 0.0

        # 地面判定
        if self.isGrounding:
            self.max_speed = self.MAX_SPEED_X

        # 最大速度
        self.x_speed = np.clip(self.x_speed, -self.max_speed, self.max_speed)
        self.y_speed = np.clip(self.y_speed, -self.MAX_SPEED_Y, self.MAX_SPEED_Y)

        # 画面外に出ないようにする
        if (self.player_x + self.x_speed < 0) and not (pressed_key[K_RIGHT] and self.x_speed >= 0):
            self.x_speed = 0.0
            self.player_x = 0
        if (self.player_x + self.x_speed > 450) and not (pressed_key[K_LEFT] and self.x_speed <= 0):
            self.x_speed = 0.0
            self.player_x = 450

        # 当たり判定
        bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
              'triangle', 'goal_pole']
        self.isGrounding = self.collision_y(stage, bg)
        self.collision_x(stage, bg)

        self.y_speed += self.FALL_ACCELERATION
        self.player_y += self.y_speed
        self.player_x += self.x_speed

        # 画面スクロール
        if self.player_x >= 210:
            # スクロール上限
            if self.scroll_sum < self.SCROLL_LIMIT:
                self.player_x = 210.0
                self.scroll = int(self.x_speed)
                self.scroll_sum += self.scroll
            else:
                self.scroll = 0

        self.draw()

    # 描画
    def draw(self):
        self.rect.left = int(self.player_x)
        self.rect.top = int(self.player_y)
        self.screen.blit(self.animation(self.img_number), self.rect)

    # x方向の当たり判定
    def collision_x(self, stage, bg):
        if self.x_speed == 0:
            return False

        width = self.rect.width
        height = self.rect.height

        # 移動先の座標と矩形を求める
        start_x = (self.player_x + self.x_speed) + self.rect_size_x
        start_y = self.player_y + self.rect_size_y
        end_x = width - self.rect_size_x
        end_y = height - self.rect_size_y

        new_rect = Rect(start_x, start_y, end_x, end_y)

        for block in stage.image_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in bg:
                # 右にあるブロック
                if self.x_speed > 0.0:
                    self.player_x = block.rect.left - width
                    self.x_speed = 0.0
                    return True

                # 左にあるブロック
                elif self.x_speed < 0.0:
                    self.player_x = block.rect.right - self.rect_size_x
                    self.x_speed = 0.0
                    return True

        return False

    # y方向の当たり判定
    def collision_y(self, stage, bg):
        if self.y_speed == 0:
            return False

        width = self.rect.width
        height = self.rect.height

        # 移動先の座標と矩形を求める
        start_x = self.player_x + self.rect_size_x
        start_y = (self.player_y + self.y_speed + self.FALL_ACCELERATION*2) + self.rect_size_y
        end_x = width - self.rect_size_x
        end_y = height - self.rect_size_y

        new_rect = Rect(start_x, start_y, end_x, end_y)

        for block in stage.image_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in bg:
                # 下にあるブロック
                if self.y_speed > 0.0:
                    self.player_y = block.rect.top - height
                    self.y_speed = 0.0
                    return True

                # 上にあるブロック
                elif self.y_speed < 0.0:
                    self.player_y = block.rect.bottom
                    self.y_speed = 0.0
                    self.img_number = 2
                    return False

        self.img_number = 2
        return False
