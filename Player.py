import pygame
from pygame.locals import *
import numpy as np

from Image import LoadImage
from Item import BlockBreak, BlockCoin
from Sound import Sound
from Stage import Stage


class Player:
    def __init__(self, screen):
        self.screen = screen

        # プレイヤースプライトからデータ読み込み
        self.sprite = Stage.player_object

        self.sprite.x_speed = self.sprite.y_speed = 0.0  # 速度
        self.ACCELERATION = 0.1  # 加速度
        self.DASH_ACCELERATION = 0.13  # ダッシュ時・空中反転時の加速度
        self.TURN_ACCELERATION = 0.21  # 地面反転時の加速度
        self.FRICTION_ACCELERATION = 0.15  # 地面摩擦時の減速度
        self.MAX_SPEED_X = 4  # x方向の最大速度
        self.MAX_SPEED_Y = 9  # y方向の最大速度
        self.sprite.AIR_MAX_SPEED = self.MAX_SPEED_X - 1  # 空中加速時の最大速度
        self.sprite.max_speed = 0  # x方向の最大速度 （変数）

        self.SCROLL_LIMIT = 3605  # 画面スクロール上限
        self.sprite.scroll = 0  # 1フレームの画面スクロール値
        self.sprite.scroll_sum = 0  # 画面スクロール量の合計

        self.sprite.isGrounding = True  # 地面に着地しているか
        self.FALL_ACCELERATION = 0.25  # 落下加速度

        self.sprite.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -6.5  # ジャンプ速度
        self.sprite.JUMP_SPEED = self.JUMP_SPEED  # ジャンプ速度 （スプライト用２セット）
        self.ADD_JUMP_SPEED = -2.0  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -1.0  # 追加のダッシュジャンプ速度
        self._jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか

        self._img_number = 0  # x座標が20変わるごとに画像を切り替え
        self._direction = None  # 向きに応じて画像を切り替え

        self.sprite.isDeath = False  # 敵に当たったかどうか
        self._death_init = True  # 初期化
        self._death_count = 0  # 静止時間を計るタイマー

        self.block_animation_list = []  # ブロックアニメーションのオブジェクトを格納するリスト

        # 当たり判定を行わない背景画像
        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']

    def update(self):
        # 死亡アニメーション時は戻る
        if self.sprite.isDeath:
            return

        pressed_key = pygame.key.get_pressed()

        # 画像アニメーション
        self._img_number = int((self.sprite.x + self.sprite.scroll_sum) / 20) % 2
        self._direction = (lambda num: self.sprite.img_left[num] if self.isLeft else self.sprite.img_right[num])

        # 地面判定
        if self.sprite.isGrounding:
            self.sprite.max_speed = self.MAX_SPEED_X

        # ジャンプ
        jump_key = pressed_key[K_UP] or pressed_key[K_z]
        if jump_key and self.sprite.isGrounding:
            if not self.sprite.isJump:
                Sound.play_SE('jump')
            self.sprite.isJump = True
            self._jump_time = 0
            self.sprite.y_speed = self.JUMP_SPEED

            # 空中時の最大速度を計算
            self.sprite.limit_air_speed()

        # 土管に入る
        elif pressed_key[K_DOWN]:
            pass

        # 8フレーム以内にキーを離した場合小ジャンプ
        if not jump_key:
            self.sprite.isJump = False
            self._jump_time = 0
        elif self.sprite.isJump:
            # 8フレーム以上キー長押しで大ジャンプ
            if self._jump_time >= 8:
                self.sprite.y_speed += self.ADD_JUMP_SPEED
                self.sprite.isJump = False
                # 移動スピードが最大の時、更にジャンプの高さを追加
                if abs(self.sprite.x_speed) == self.MAX_SPEED_X:
                    self.sprite.y_speed += self.ADD_DASH_JUMP_SPEED
            else:
                self._jump_time += 1

        # 左移動
        if pressed_key[K_LEFT]:
            if self.sprite.x_speed < -1:
                self.sprite.x_speed -= self.ACCELERATION
            elif self.sprite.x_speed > 0 and self.sprite.isGrounding:
                self.sprite.x_speed -= self.TURN_ACCELERATION
            else:
                self.sprite.x_speed -= self.DASH_ACCELERATION

            self.isLeft = True

        # 右移動
        elif pressed_key[K_RIGHT]:
            if self.sprite.x_speed > 1:
                self.sprite.x_speed += self.ACCELERATION
            elif self.sprite.x_speed < 0 and self.sprite.isGrounding:
                self.sprite.x_speed += self.TURN_ACCELERATION
            else:
                self.sprite.x_speed += self.DASH_ACCELERATION

            self.isLeft = False

        # 地面摩擦
        elif self.sprite.isGrounding:
            if abs(self.sprite.x_speed) > 0.1:
                self.sprite.x_speed -= self.FRICTION_ACCELERATION * np.sign(self.sprite.x_speed)
            else:
                self.sprite.x_speed = 0.0

        # 最大速度
        self.sprite.x_speed = np.clip(self.sprite.x_speed, -self.sprite.max_speed, self.sprite.max_speed)
        self.sprite.y_speed = np.clip(self.sprite.y_speed, None, self.MAX_SPEED_Y)

        # 画面外に出ないようにする
        if (self.sprite.x + self.sprite.x_speed < 0) and not (pressed_key[K_RIGHT] and self.sprite.x_speed >= 0):
            self.sprite.x_speed = 0.0
            self.sprite.x = 0
        if (self.sprite.x + self.sprite.x_speed > 450) and not (pressed_key[K_LEFT] and self.sprite.x_speed <= 0):
            self.sprite.x_speed = 0.0
            self.sprite.x = 450

        # 当たり判定
        self.sprite.isGrounding = self.collision_y()
        isHit_x = self.collision_x()

        self.sprite.y_speed += self.FALL_ACCELERATION
        self.sprite.y += self.sprite.y_speed
        self.sprite.x += self.sprite.x_speed

        # 画面スクロール
        if self.sprite.x >= 210 and not isHit_x:
            # スクロール上限
            if self.sprite.scroll_sum < self.SCROLL_LIMIT:
                self.sprite.x = 210.0
                self.sprite.scroll = np.round(self.sprite.x_speed)
                self.sprite.scroll_sum += self.sprite.scroll
            else:
                self.sprite.scroll = 0

        # 画面外に落下したら死亡
        if self.sprite.y > 500:
            self.sprite.isDeath = True

        self.sprite.update(self._direction(self._img_number))
        self.animation()

    # スプライト以外のアニメーション
    def animation(self):
        # ブロックを叩いた時のアニメーション
        for animation in self.block_animation_list:
            animation.update()
            if animation.isSuccess:
                self.block_animation_list.remove(animation)

    # 死亡時のアニメーション
    def death(self):
        if self.sprite.isDeath:
            if self._death_init:
                self._death_init = False

                Sound.stop_BGM()
                Sound.play_SE('death')

                self.sprite.x_speed = 0.0
                self.sprite.scroll = 0

                self._img_number = 3
                self._jump_time = 0
                self.sprite.y_speed = self.JUMP_SPEED

            self._jump_time += 1

            # 20フレーム後に落下
            if self._jump_time >= 20:
                self.sprite.y_speed += self.FALL_ACCELERATION
                self.sprite.y += self.sprite.y_speed

            # 時間が経過したら戻って残機表示
            if self._jump_time >= 210:
                return True

            self.sprite.update(self._direction(self._img_number))
            self.animation()

        return False

    # x方向の当たり判定
    def collision_x(self):
        isHit_x = False

        # 移動先の座標と矩形を求める
        start_x = 3 + self.sprite.x + self.sprite.x_speed - self.sprite.scroll
        start_y = self.sprite.y + self.sprite.y_speed + self.FALL_ACCELERATION * 2 + 8
        end_x = self.sprite.width / 2
        end_y = self.sprite.height - 24

        new_rect_left = Rect(start_x, start_y, end_x, end_y)
        new_rect_right = Rect(start_x + end_x - 3, start_y, end_x, end_y)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_left)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_right)

        for block in Stage.block_object_list:
            # 当たり判定に背景画像・隠しブロックを除く
            if block.name not in self.bg and not block.isHide:
                # 左にある場合
                collide_left = new_rect_left.colliderect(block.rect)
                if collide_left:
                    self.block_animation('LR', block)
                    self.sprite.x_speed = 0.0
                    self.sprite.scroll = 0
                    isHit_x = True

                    if self.sprite.x != 1 + block.rect.left - self.sprite.width:
                        self.sprite.x = block.rect.right - 3

                # 右にある場合
                collide_right = new_rect_right.colliderect(block.rect)
                if collide_right:
                    self.block_animation('LR', block)
                    self.sprite.x_speed = 0.0
                    self.sprite.scroll = 0
                    isHit_x = True

                    if self.sprite.x != block.rect.right - 3:
                        self.sprite.x = 1 + block.rect.left - self.sprite.width

        return isHit_x

    # y方向の当たり判定
    def collision_y(self):
        # 移動先の座標と矩形を求める
        start_x = self.sprite.x + self.sprite.x_speed - self.sprite.scroll
        start_y = self.sprite.y + self.sprite.y_speed + self.FALL_ACCELERATION * 2 + 3
        end_x = self.sprite.width
        end_y = self.sprite.height / 4

        new_rect_top = Rect(start_x + 9, start_y, end_x - 18, end_y)
        new_rect_bottom = Rect(start_x + 5, start_y + end_y * 3, end_x - 10, end_y)
        new_rect_block = Rect(start_x + 1, start_y - 15, end_x - 2, end_y)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_top)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_bottom)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_block)

        for block in Stage.block_object_list:
            collide_top = new_rect_top.colliderect(block.rect)
            collide_bottom = new_rect_bottom.colliderect(block.rect)
            collide_block = new_rect_block.colliderect(block.rect)

            if block.name not in self.bg:
                # 叩けないブロック
                if collide_block and self.sprite.y_speed < 0 and not block.isHide:
                    self.block_animation('TOP_BLOCK', block)

                # 上にある場合
                if collide_top and self.sprite.y_speed < 0:
                    self.block_animation('TOP', block)
                    if not block.isHide and not block.data == 18:
                        self.sprite.y = block.rect.bottom
                        self.sprite.y_speed /= -5
                        self._img_number = 2
                    return False

                # 下にある場合
                if collide_bottom and self.sprite.y_speed > 0 and not block.isHide:
                    self.block_animation('BOTTOM', block)
                    self.sprite.y = block.rect.top - self.sprite.height
                    self.sprite.y_speed = 0.0
                    return True

        self._img_number = 2
        return False

    def block_animation(self, direction, block):
        # 壊れるブロック
        if block.name == 'block1':
            # 叩くとトゲを生やす
            if block.data == 2:
                block.isThorns = True
                self.sprite.isDeath = True

            if direction == 'TOP':
                # 叩くと壊れる
                if block.data == 1:
                    Sound.play_SE('brockbreak')
                    self.block_animation_list.append(BlockBreak(self.screen, block))
                    block.remove()
                    Stage.block_object_list.remove(block)

        # はてなブロック
        if block.name == 'block2':
            if direction == 'TOP':
                pass
                # # 叩くとコインが出る
                # if block.data == 17:
                #     Sound.play_SE('coin')
                #     self.block_animation_list.append(BlockCoin(self.screen, block))
                #     block.name = 'block3'
                #     block.data = 29
                #     block.image = LoadImage.image_list[block.name]

            # 叩けないブロック
            # elif direction == 'TOP_BLOCK' and block.data == 18 and self.sprite.y_speed < 0:
            #     block.rect.bottom += self.sprite.y_speed

        # 隠しブロック
        # if block.name == 'block3' and direction == 'TOP' and block.isHide and self.sprite.y_speed < 0:
        #     Sound.play_SE('coin')
        #     self.block_animation_list.append(BlockCoin(self.screen, block))
        #     block.isHide = False
