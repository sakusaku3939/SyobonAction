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

        x_speed: float
        y_speed: float
        self.x_speed = self.y_speed = 0.0  # 速度
        self.ACCELERATION = 0.08  # 加速度
        self.DASH_ACCELERATION = 0.26  # 反転ダッシュ時の加速度
        self.FRICTION_ACCELERATION = 0.13  # 地面摩擦時の減速度
        self.MAX_SPEED = 4.0  # 最大速度

        self.SCROLL_LIMIT = 3605  # 画面スクロール上限
        self.scroll_sum = 0  # 画面スクロール量の合計

        self.isGrounding = True  # 落下しているか
        self.FALL_ACCELERATION = 0.3  # 落下加速度

        self.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -7.0  # ジャンプ速度
        self.ADD_JUMP_SPEED = -2.0  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -1.2  # 追加のダッシュジャンプ速度
        self.jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか
        self.isHIT_Head = False  # 頭がブロックに当たったか

        self.img_number = 0  # x座標が20変わるごとに画像を切り替え
        self.animation = None  # 向きに応じて画像を切り替え

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
            self.player_y -= 3
            self.y_speed = self.JUMP_SPEED

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
                if abs(self.x_speed) == self.MAX_SPEED:
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
            self.x_speed -= self.FRICTION_ACCELERATION * np.sign(self.x_speed)

        # 最大速度
        self.x_speed = np.clip(self.x_speed, -self.MAX_SPEED, self.MAX_SPEED)

        # 画面外に出ないようにする
        if (self.player_x + self.x_speed < 0) and not (pressed_key[K_RIGHT] and self.x_speed >= 0):
            self.x_speed = 0.0
            self.player_x = 0
        if (self.player_x + self.x_speed > 450) and not (pressed_key[K_LEFT] and self.x_speed <= 0):
            self.x_speed = 0.0
            self.player_x = 450

        # 画面スクロール
        if self.player_x >= 210:
            # スクロール上限
            if self.scroll_sum < self.SCROLL_LIMIT:
                self.player_x = 210
                self.scroll = int(self.x_speed)
                self.scroll_sum += self.scroll
            else:
                self.scroll = 0

        # 当たり判定
        bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
              'triangle']
        collision_name_x, sign_x = self.collision_x(stage, bg)
        collision_name_y, sign_y = self.collision_y(stage, bg)

        print(collision_name_y)

        # 地面判定
        if collision_name_y == '':
            self.player_y += self.y_speed
            self.isGrounding = False
            self.y_speed += self.FALL_ACCELERATION
            self.img_number = 2
        else:
            # 頭上にブロックがあった場合
            if sign_y == -1:
                self.isHIT_Head = True
                self.player_y += 5
                self.y_speed = 0
            else:
                self.y_speed = 0.0
                self.isHIT_Head = False
                self.isGrounding = True
            self.isJump = False

        # x方向の当たり判定
        if collision_name_x == '':
            self.player_x += self.x_speed

        self.draw()

    # 描画
    def draw(self):
        self.rect.left = int(self.player_x)
        self.rect.top = int(self.player_y)
        self.screen.blit(self.animation(self.img_number), self.rect)

    # x方向の当たり判定
    def collision_x(self, stage, bg):
        width = self.rect.width
        height = self.rect.height
        sign = np.sign(int(self.x_speed))

        # x方向の移動先の座標と矩形を求める
        new_x = self.player_x + self.x_speed
        new_rect = Rect(new_x + 5, self.player_y + 5, width - 5, height - 10)

        # ブロックとの衝突判定
        for block in stage.image_object_list:
            collide = new_rect.colliderect(block.rect)
            # 衝突するブロックあり
            if collide and block.name not in bg and sign != 0:
                self.x_speed = 0.0
                return block.name, sign
        return '', 0

    # y方向の当たり判定
    def collision_y(self, stage, bg):
        width = self.rect.width
        height = self.rect.height

        sign = np.sign(int(self.y_speed))

        # y方向の移動先の座標と矩形を求める
        new_y = self.player_y + self.y_speed
        new_rect = Rect(self.player_x + 6, new_y + 5, width - 12, height - 5)

        # ブロックとの衝突判定
        for block in stage.image_object_list:
            collide = new_rect.colliderect(block.rect)
            # 衝突するブロックあり
            if collide and block.name not in bg and sign != 0:
                self.player_y = block.y - 34.0 * sign
                return block.name, sign
        return '', 0
