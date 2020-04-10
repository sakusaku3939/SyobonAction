import pygame
from pygame.locals import *
import numpy as np

from Image import LoadImage
from Stage import Stage


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
        self.img_left = [pygame.transform.flip(img, True, False) for img in self.img_right]

        self.player_x = 80
        self.player_y = 320
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = Rect(self.player_x, self.player_y, self.width, self.height)

        self.x_speed = self.y_speed = 0.0  # 速度
        self.ACCELERATION = 0.1  # 加速度
        self.DASH_ACCELERATION = 0.18  # ダッシュ時の加速度
        self.TURN_ACCELERATION = 0.22  # 反転時の加速度
        self.FRICTION_ACCELERATION = 0.15  # 地面摩擦時の減速度
        self.MAX_SPEED_X = 4  # x方向の最大速度
        self.MAX_SPEED_Y = 9  # y方向の最大速度
        self.max_speed = 0  # 最大速度 （変数）

        self.SCROLL_LIMIT = 3605  # 画面スクロール上限
        self.scroll_sum = 0  # 画面スクロール量の合計

        self.isGrounding = True  # 地面に着地しているか
        self.FALL_ACCELERATION = 0.27  # 落下加速度

        self.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -6.7  # ジャンプ速度
        self.ADD_JUMP_SPEED = -2.3  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -0.8  # 追加のダッシュジャンプ速度
        self.jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか
        self.isHIT_Head = False  # 頭がブロックに当たったか

        self.img_number = 0  # x座標が20変わるごとに画像を切り替え
        self.animation = None  # 向きに応じて画像を切り替え

        # 当たり判定を行わない背景画像
        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']

    def update(self):
        pressed_key = pygame.key.get_pressed()

        # 画像アニメーション
        self.img_number = int((self.player_x + self.scroll_sum) / 20) % 2
        self.animation = (lambda num: self.img_left[num] if self.isLeft else self.img_right[num])

        # 地面判定
        if self.isGrounding:
            self.max_speed = self.MAX_SPEED_X

        # ジャンプ
        jump_key = pressed_key[K_UP] or pressed_key[K_z]
        if jump_key and self.isGrounding:
            self.isJump = True
            self.jump_time = 0
            self.y_speed = self.JUMP_SPEED
            if abs(self.x_speed) < self.MAX_SPEED_X - 1:
                self.max_speed = self.MAX_SPEED_X - 1
            else:
                self.max_speed = abs(self.x_speed)

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
            if self.x_speed < -1:
                self.x_speed -= self.ACCELERATION
            elif self.x_speed > 0 and self.isGrounding:
                self.x_speed -= self.TURN_ACCELERATION
            else:
                self.x_speed -= self.DASH_ACCELERATION

            self.isLeft = True

        # 右移動
        elif pressed_key[K_RIGHT]:
            if self.x_speed > 1:
                self.x_speed += self.ACCELERATION
            elif self.x_speed < 0 and self.isGrounding:
                self.x_speed += self.TURN_ACCELERATION
            else:
                self.x_speed += self.DASH_ACCELERATION
            # self.x_speed += self.ACCELERATION if self.x_speed > 1 else self.DASH_ACCELERATION
            self.isLeft = False

        # 地面摩擦
        elif self.isGrounding:
            if abs(self.x_speed) > 0.1:
                self.x_speed -= self.FRICTION_ACCELERATION * np.sign(self.x_speed)
            else:
                self.x_speed = 0.0

        # 最大速度
        self.x_speed = np.clip(self.x_speed, -self.max_speed, self.max_speed)
        self.y_speed = np.clip(self.y_speed, None, self.MAX_SPEED_Y)

        # 画面外に出ないようにする
        if (self.player_x + self.x_speed < 0) and not (pressed_key[K_RIGHT] and self.x_speed >= 0):
            self.x_speed = 0.0
            self.player_x = 0
        if (self.player_x + self.x_speed > 450) and not (pressed_key[K_LEFT] and self.x_speed <= 0):
            self.x_speed = 0.0
            self.player_x = 450

        # 当たり判定
        self.isGrounding = self.collision_y()
        isHit_x = self.collision_x()

        self.y_speed += self.FALL_ACCELERATION
        self.player_y += self.y_speed
        self.player_x += self.x_speed

        # 画面スクロール
        if self.player_x >= 210 and not isHit_x:
            # スクロール上限
            if self.scroll_sum < self.SCROLL_LIMIT:
                self.player_x = 210.0
                self.scroll = np.round(self.x_speed)
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
    def collision_x(self):
        # 移動先の座標と矩形を求める
        start_x = self.player_x + self.x_speed
        start_y = self.player_y + self.FALL_ACCELERATION * 2 + 15
        end_x = self.width / 2
        end_y = self.height - 30

        new_rect_left = Rect(start_x, start_y, end_x, end_y)

        start_x += self.width / 2
        new_rect_right = Rect(start_x, start_y, end_x, end_y)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_left)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_right)

        for block in Stage.block_object_list:
            collide_left = new_rect_left.colliderect(block.rect)
            collide_right = new_rect_right.colliderect(block.rect)
            if block.name not in self.bg:
                # 両隣にある場合
                if collide_left and collide_right:
                    self.x_speed = 0.0
                    self.scroll = 0
                    return True

                # 右にある場合
                elif collide_right and self.x_speed > 0.0:
                    self.player_x = block.rect.left - self.width
                    self.x_speed = 0.0
                    self.scroll = 0
                    return True

                # 左にある場合
                elif collide_left and self.x_speed < 0.0:
                    self.player_x = block.rect.right
                    self.x_speed = 0.0
                    self.scroll = 0
                    return True

        return False

    # y方向の当たり判定
    def collision_y(self):
        # 移動先の座標と矩形を求める
        start_x = self.player_x + 8
        start_y = self.player_y + self.y_speed + self.FALL_ACCELERATION * 2 + 3
        end_x = self.width - 14
        end_y = self.height - 1

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect)  # 当たり判定可視化 （デバック用）

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
                # 下にある場合
                if self.y_speed > 0.0:
                    self.player_y = block.rect.top - self.height
                    self.y_speed = 0.0
                    return True

                # 上にある場合
                elif self.y_speed < 0.0:
                    self.player_y = block.rect.bottom
                    self.y_speed = 0.0
                    self.img_number = 2
                    return False

        self.img_number = 2
        return False
