import pygame
from pygame.locals import *
import numpy as np

import Block
from Sprite import SpritePlayer
from Sound import Sound
from Stage import Stage


class Player:
    def __init__(self, screen, stage):
        self.screen = screen
        self.stage = stage

        # プレイヤースプライトからデータ読み込み
        self.player = Stage.player_object

        self.player.x_speed = self.player.y_speed = 0.0  # 速度
        self.ACCELERATION = 0.08  # 加速度
        self.DASH_ACCELERATION = 0.14  # ダッシュ時・空中反転時の加速度
        self.TURN_ACCELERATION = 0.21  # 地面反転時の加速度
        self.FRICTION_ACCELERATION = 0.15  # 地面摩擦時の減速度
        self.MAX_SPEED_X = 4  # x方向の最大速度
        self.MAX_SPEED_Y = 9  # y方向の最大速度
        self.player.AIR_MAX_SPEED = self.MAX_SPEED_X - 1  # 空中加速時の最大速度
        self.player.max_speed = 0  # x方向の最大速度 （変数）

        # 画面スクロール上限
        self.SCROLL_LIMIT = 3605

        self.player.isGrounding = True  # 地面に着地しているか
        self.FALL_ACCELERATION = 0.25  # 落下加速度

        self.player.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -6.5  # ジャンプ速度
        self.player.JUMP_SPEED = self.JUMP_SPEED  # ジャンプ速度 （スプライト用２セット）
        self.ADD_JUMP_SPEED = -2.0  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -0.8  # 追加のダッシュジャンプ速度
        self._jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか

        self._img_number = 0  # x座標が20変わるごとに画像を切り替え
        self._direction = None  # 向きに応じて画像を切り替え

        self.player.isDeath = False  # 敵に当たったかどうか
        self._death_init = True  # 初期化
        self._death_count = 0  # 静止時間を計るタイマー

        self.item_animation_list = []  # ブロックアニメーションのオブジェクトを格納するリスト

        # 当たり判定を行わない背景画像
        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']

    def update(self):
        # 死亡アニメーション中は戻る
        if self.player.isDeath:
            return

        pressed_key = pygame.key.get_pressed()

        # 画像アニメーション
        self._img_number = int((self.player.x + SpritePlayer.scroll_sum) / 20) % 2
        self._direction = (lambda num: self.player.img_left[num] if self.isLeft else self.player.img_right[num])

        # 地面判定
        if self.player.isGrounding:
            self.player.max_speed = self.MAX_SPEED_X

        # ジャンプ
        jump_key = pressed_key[K_UP] or pressed_key[K_z]
        if jump_key and self.player.isGrounding:
            if not self.player.isJump:
                Sound.play_SE('jump')
            self.player.isJump = True
            self._jump_time = 0
            self.player.y_speed = self.JUMP_SPEED

            # 空中時の最大速度を計算
            self.player.limit_air_speed()

        # 土管に入る
        elif pressed_key[K_DOWN]:
            pass

        # 8フレーム以内にキーを離した場合小ジャンプ
        if not jump_key:
            self.player.isJump = False
            self._jump_time = 0
        elif self.player.isJump:
            # 8フレーム以上キー長押しで大ジャンプ
            if self._jump_time >= 8:
                self.player.y_speed += self.ADD_JUMP_SPEED
                self.player.isJump = False
                # 移動スピードが最大の時、更にジャンプの高さを追加
                if abs(self.player.x_speed) == self.MAX_SPEED_X:
                    self.player.y_speed += self.ADD_DASH_JUMP_SPEED
            else:
                self._jump_time += 1

        # 左移動
        if pressed_key[K_LEFT]:
            if self.player.x_speed < -1:
                self.player.x_speed -= self.ACCELERATION
            elif self.player.x_speed > 0 and self.player.isGrounding:
                self.player.x_speed -= self.TURN_ACCELERATION
            else:
                self.player.x_speed -= self.DASH_ACCELERATION

            self.isLeft = True

        # 右移動
        elif pressed_key[K_RIGHT]:
            if self.player.x_speed > 1:
                self.player.x_speed += self.ACCELERATION
            elif self.player.x_speed < 0 and self.player.isGrounding:
                self.player.x_speed += self.TURN_ACCELERATION
            else:
                self.player.x_speed += self.DASH_ACCELERATION

            self.isLeft = False

        # 地面摩擦
        elif self.player.isGrounding:
            if abs(self.player.x_speed) > 0.1:
                self.player.x_speed -= self.FRICTION_ACCELERATION * np.sign(self.player.x_speed)
            else:
                self.player.x_speed = 0.0

        # 最大速度
        self.player.x_speed = np.clip(self.player.x_speed, -self.player.max_speed, self.player.max_speed)
        self.player.y_speed = np.clip(self.player.y_speed, None, self.MAX_SPEED_Y)

        # 画面外に出ないようにする
        if (self.player.x + self.player.x_speed < 0) and not (pressed_key[K_RIGHT] and self.player.x_speed >= 0):
            self.player.x_speed = 0.0
            self.player.x = 0
        if (self.player.x + self.player.x_speed > 450) and not (pressed_key[K_LEFT] and self.player.x_speed <= 0):
            self.player.x_speed = 0.0
            self.player.x = 450

        # 当たり判定
        self.player.isGrounding = self.collision_y()
        self.collision_x()

        self.player.y_speed += self.FALL_ACCELERATION
        self.player.y += self.player.y_speed
        self.player.x += self.player.x_speed

        if self.player.x >= 210:
            # スクロール上限
            if SpritePlayer.scroll_sum < self.SCROLL_LIMIT:
                self.player.x = 210
                SpritePlayer.scroll = round(self.player.x_speed)
                SpritePlayer.scroll_sum += SpritePlayer.scroll
            else:
                SpritePlayer.scroll = 0

        # 画面外に落下したら死亡
        if self.player.y > 500:
            self.player.isDeath = True

        self.bg_update()
        self.player.update(self._direction(self._img_number))

    # 背景画像の描画
    def bg_update(self):
        for image in Stage.block_object_list:
            if image.name in self.bg:
                image.update()

    # アイテムなどのアニメーション
    def item_animation(self):
        for animation in self.item_animation_list:
            animation.update()

            # 新たに生成するか
            if animation.isGenerate:
                animation.isGenerate = False
                self.item_animation_list.append(Block.PoisonKinoko(self.screen, animation.block, isLot=True))

            # アニメーションが完了したか
            if animation.isSuccess:
                self.item_animation_list.remove(animation)

    # 死亡時のアニメーション
    def death(self):
        if self.player.isDeath:
            if self._death_init:
                self._death_init = False

                Sound.stop_BGM()
                Sound.play_SE('death')

                self.player.x_speed = 0.0
                SpritePlayer.scroll = 0

                self._img_number = 3
                self._jump_time = 0
                self.player.y_speed = self.JUMP_SPEED

            self._jump_time += 1

            # 20フレーム後に落下
            if self._jump_time >= 20:
                self.player.y_speed += self.FALL_ACCELERATION
                self.player.y += self.player.y_speed

            # 時間が経過したら戻って残機表示
            if self._jump_time >= 210:
                return True

            self.bg_update()
            self.player.update(self._direction(self._img_number))

        return False

    # x方向の当たり判定
    def collision_x(self):
        x = self.player.rect.left + self.player.x_speed
        y = self.player.y + self.player.y_speed

        # 移動先の座標と矩形を求める
        start_x = (x - SpritePlayer.scroll) + 3
        start_y = y + self.FALL_ACCELERATION * 2 + 8
        end_x = self.player.width / 2
        end_y = self.player.height - 24

        new_rect_left = Rect(start_x, start_y, end_x, end_y)
        new_rect_right = Rect(start_x + end_x - 4, start_y, end_x, end_y)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_left)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_right)

        for block in Stage.block_object_list:
            collide_right = new_rect_right.colliderect(block.rect)
            collide_left = new_rect_left.colliderect(block.rect)

            # 当たり判定に背景画像・隠しブロックを除く
            if block.name not in self.bg and not block.isHide:
                # pygame.draw.rect(self.screen, (255, 0, 0), block.rect)  # 当たり判定可視化 （デバック用）

                # 左にある場合
                if collide_left:
                    self.block_animation('LR', block)

                    if self.player.x != 2 + block.rect.left - self.player.width and not self.player.x_speed > 0:
                        self.player.x_speed = 0.0
                        SpritePlayer.scroll = 0
                        self.player.x = block.rect.right - 3

                # 右にある場合
                if collide_right:
                    self.block_animation('LR', block)

                    if self.player.x != block.rect.right - 4 and not self.player.x_speed < 0:
                        self.player.x_speed = 0.0
                        SpritePlayer.scroll = 0
                        self.player.x = 2 + block.rect.left - self.player.width

            # 背景画像のアニメーション
            elif collide_left or collide_right:
                self.block_animation('', block)

    # y方向の当たり判定
    def collision_y(self):
        x = self.player.rect.left + self.player.x_speed
        y = self.player.y + self.player.y_speed

        # 移動先の座標と矩形を求める
        start_x = x - SpritePlayer.scroll
        start_y = y + self.FALL_ACCELERATION * 2 + 3
        end_x = self.player.width
        end_y = self.player.height / 4

        new_rect_top = Rect(start_x + 10, self.player.y, end_x - 18, end_y)
        new_rect_bottom = Rect(start_x + 6, start_y + end_y * 3, end_x - 10, end_y)
        new_rect_block = Rect(start_x + 1, start_y - 10, end_x - 2, end_y * 3)

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
                if collide_block and self.player.y_speed < 0 and not block.isHide:
                    self.block_animation('TOP_BLOCK', block)

                # 上にある場合
                if collide_top and self.player.y_speed < 0 and not self.player.isGrounding:
                    self.block_animation('TOP', block)
                    if not block.isHide and not block.data == 18:
                        self.player.y = block.rect.bottom
                        self.player.y_speed /= -3
                        self._img_number = 2
                    return False

                # 下にある場合
                if collide_bottom and self.player.y_speed > 0 and not block.isHide:
                    self.block_animation('BOTTOM', block)
                    self.player.y = block.rect.top - self.player.height + 1
                    self.player.y_speed = 0.0
                    return True

            # 背景画像のアニメーション
            elif collide_top or collide_bottom:
                self.block_animation('', block)

        self._img_number = 2
        return False

    # ブロックのアニメーション
    def block_animation(self, direction, block):
        def add_block(function):
            self.item_animation_list.append(function)

        # 壊れるブロック
        if block.name == 'block1':
            # 叩くとトゲを生やす
            if block.data == 1.1:
                block.isThorns = True
                self.player.isDeath = True

            if direction == 'TOP':
                # 叩くと壊れる
                if block.data == 1:
                    add_block(Block.Break(self.screen, block))
                    block.remove()
                    Stage.block_object_list.remove(block)

        # はてなブロック
        if block.name == 'block2':
            if direction == 'TOP':
                # 叩くとコインが出る
                if block.data == 3:
                    add_block(Block.Coin(self.screen, block))

                # 叩くと赤キノコが出る
                if block.data == 3.2:
                    add_block(Block.Kinoko(self.screen, block))

                # 叩くと敵が出る
                if block.data == 3.8:
                    add_block(Block.Enemy(self.screen, block, 'enemy'))

            # 叩けないブロック
            elif direction == 'TOP_BLOCK' and block.data == 3.1 and self.player.y_speed < 0:
                block.rect.bottom = self.player.rect.top - 10

        # 隠しブロック
        if block.name == 'block3' and direction == 'TOP' and block.isHide and self.player.y_speed < 0:
            block.isHide = False
            # 叩くとコインが出る
            if block.data == 5:
                add_block(Block.Coin(self.screen, block))

            # 叩くと大量の毒キノコが出る
            if block.data == 5.5:
                add_block(Block.PoisonKinoko(self.screen, block, isLot=True))

        if block.name == 'halfway' and direction == '':
            SpritePlayer.initial_x = 210
            SpritePlayer.initial_y = block.y
            SpritePlayer.initial_scroll_sum = block.x - 210
            block.remove()
            Stage.block_object_list.remove(block)
