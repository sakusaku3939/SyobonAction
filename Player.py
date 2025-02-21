import pygame
from pygame.locals import *
import numpy as np

import Block
from Image import LoadImage
from Sprite import SpritePlayer, SpriteBlock
from Sound import Sound
from Stage import Stage
from Text import Text
from model.PolicyNetwork import SimpleRewardSystem


class Player:
    def __init__(self, screen, stage, is_ai_mode=False):
        self.screen = screen
        self.stage = stage
        self.is_ai_mode = is_ai_mode
        self.stack_time = 0
        self.latest_scroll_sum = 0

        self.reward_system = SimpleRewardSystem()

        # プレイヤースプライトからデータ読み込み
        self.player = Stage.player_object

        self.player.x_speed = self.player.y_speed = 0.0  # 速度
        self.ACCELERATION = 0.1  # 加速度
        self.DASH_ACCELERATION = 0.14  # ダッシュ時・空中反転時の加速度
        self.TURN_ACCELERATION = 0.22  # 地面反転時の加速度
        self.FRICTION_ACCELERATION = 0.15  # 地面摩擦時の減速度
        self.MAX_SPEED_X = 4  # x方向の最大速度
        self.MAX_SPEED_Y = 9  # y方向の最大速度
        self.player.max_speed = 0  # x方向の最大速度 （変数）
        self.SCROLL_LIMIT = 3605  # 画面スクロール上限

        self.player.isGrounding = True  # 地面に着地しているか
        self.player.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -6.0  # ジャンプ速度
        self.player.JUMP_SPEED = self.JUMP_SPEED  # ジャンプ速度 （スプライト用にセット）
        self.ADD_JUMP_SPEED = -2.3  # 追加のジャンプ速度
        self.ADD_DASH_JUMP_SPEED = -1.0  # 追加のダッシュジャンプ速度
        self._jump_time = 0  # ジャンプ時間

        self.isLeft = False  # 左を向いているかどうか

        self._img_number = 0  # x座標が20変わるごとに画像を切り替え
        self._direction = None  # 向きに応じて画像を切り替え

        self.player.isDeath = False  # 敵に当たったかどうか
        self._death_init = True  # 初期化

        self.player.dive_dokan = None  # 潜っている土管を格納するオブジェクト
        self._fly_dokan = None  # 飛ぶ土管を格納するオブジェクト
        self._dokan_init = True  # 初期化
        self._dokan_count = 0  # 潜る時間を計るタイマー

        self.player.goal = None  # ゴールブロックを格納するオブジェクト
        self.goal_isMove = False  # 移動するかどうか
        self._inGoal_tower = False  # ゴール塔に入ったかどうか
        self._goal_init = True  # 初期化
        self._goal_count = 0  # ゴールの計るタイマー
        self._goal_scene_y = 500  # ゴール時に次のシーンへ移るy座標

        self.jump_disable_list = []  # ジャンプを無効にするブロックリスト
        self.item_animation_list = []  # ブロックアニメーションのオブジェクトを格納するリスト
        Block.Coin.generate_count = Block.PoisonKinoko.generate_count = 0  # 生成数を初期化

    def update(self, action=None, prev_player_movement=0):
        # print(self.player.x, self.player.y, SpritePlayer.scroll_sum)  # プレイヤー座標（デバック用）

        # 強制アニメーション中は戻る
        if not (self._death_init and self._dokan_init and (self._goal_init or self.goal_isMove)):
            return None, None, None, None

        if self.is_ai_mode:
            pressed_key = [0] * 323
            # print(action)
            if action == 0:
                pressed_key[K_LEFT] = 1
            elif action == 1:
                pressed_key[K_RIGHT] = 1
            elif action == 2:
                pressed_key[K_UP] = 1
            elif action == 3:
                pressed_key[K_LEFT] = 1
                pressed_key[K_UP] = 1
            elif action == 4:
                pressed_key[K_RIGHT] = 1
                pressed_key[K_UP] = 1
        else:
            pressed_key = pygame.key.get_pressed()

        # 画像アニメーション
        self._img_number = int((self.player.x + SpritePlayer.scroll_sum) / 20) % 2
        self._direction = (lambda num: self.player.img_right[
            num] if not self.isLeft or self.goal_isMove else self.player.img_left[num])

        # 地面判定
        if self.player.isGrounding:
            self.player.max_speed = self.MAX_SPEED_X

        # ジャンプ
        jump_key = pressed_key[K_UP] or pressed_key[K_z]
        if jump_key and self.player.isGrounding and not self.goal_isMove:
            if not self.player.isJump:
                Sound.play_SE('jump')
            self.player.isJump = True
            self._jump_time = 0
            self.player.y -= 11
            self.player.y_speed = self.JUMP_SPEED

            # 空中時の最大速度を計算
            self.player.limit_air_speed()

        # 8フレーム以内にキーを離した場合小ジャンプ
        if not jump_key:
            self.player.isJump = False
            self._jump_time = 0
        elif self.player.isJump:
            # 8フレーム以上キー長押しで大ジャンプ
            if self._jump_time >= 8:
                self.player.y_speed += self.ADD_JUMP_SPEED
                self.player.isJump = False
                # 移動スピードが一定値を超えた時、更にジャンプの高さを追加
                if abs(self.player.x_speed) > self.MAX_SPEED_X - 2:
                    self.player.y_speed += self.ADD_DASH_JUMP_SPEED
            else:
                self._jump_time += 1

        # 左移動
        if pressed_key[K_LEFT] and not self.goal_isMove:
            if self.player.x_speed < -1:
                self.player.x_speed -= self.ACCELERATION
            elif self.player.x_speed > 0 and self.player.isGrounding:
                self.player.x_speed -= self.TURN_ACCELERATION
            else:
                self.player.x_speed -= self.DASH_ACCELERATION

            self.isLeft = True

        # 右移動
        elif pressed_key[K_RIGHT] and not self.goal_isMove:
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

        self.player.y_speed += SpritePlayer.FALL_ACCELERATION
        self.player.y += self.player.y_speed
        self.player.x += self.player.x_speed

        if self.player.x >= 210:
            # スクロール上限
            if SpritePlayer.scroll_sum < self.SCROLL_LIMIT:
                self.player.x = 210
                SpritePlayer.scroll = self.player.x_speed
                SpritePlayer.scroll_sum += SpritePlayer.scroll
            else:
                SpritePlayer.scroll = 0

        # 画面外に落下したら死亡
        if self.player.y > 500:
            self.player.isDeath = True

        self.block_animation()
        self.bg_update()
        self.player.update(self._direction(self._img_number))

        # 報酬の計算
        current_position = self.player.x + SpritePlayer.scroll_sum
        reward, done = self.reward_system.calculate_reward(self.player)

        agent_pos = np.array([current_position, self.player.y])

        if SpritePlayer.scroll_sum == self.latest_scroll_sum:
            self.stack_time += 1
        else:
            self.stack_time = 0
        self.latest_scroll_sum = SpritePlayer.scroll_sum

        if self.stack_time > 300:
            self.player.isDeath = True

        return agent_pos, reward, done, current_position

    # 背景画像の描画
    def bg_update(self):
        for image in Stage.block_object_list:
            if image.name in SpriteBlock.BG:
                image.update()

    # アイテムなどのアニメーション
    def item_animation(self):
        for animation in self.item_animation_list:
            animation.update()

            # 新たに生成するか
            if animation.isGenerate:
                animation.isGenerate = False
                # 生成する個数
                if animation.__class__.generate_count < animation.GENERATE_MAX - 1 or animation.GENERATE_MAX == -1:
                    animation.__class__.generate_count += 1
                    self.item_animation_list.append(animation.__class__(self.screen, animation.block, isLot=True))
                else:
                    animation.__class__.generate_count = 0

            # アニメーションが完了したか
            if animation.isSuccess:
                self.item_animation_list.remove(animation)

    # 死亡時のアニメーション
    def death_animation(self):
        if self.player.isDeath and self.is_ai_mode:
            return True

        if self.player.isDeath:
            # 初期化
            if self._death_init:
                self._death_init = False

                Sound.stop_SE()
                Sound.stop_BGM()
                Sound.play_SE('death')

                self.player.x_speed = 0.0
                SpritePlayer.scroll = 0

                self._img_number = 3
                self._jump_time = 0
                self.player.y_speed = self.JUMP_SPEED

            self._jump_time += 1

            # 20フレーム後に落下
            if self._jump_time > 20:
                self.player.y_speed += SpritePlayer.FALL_ACCELERATION
                self.player.y += self.player.y_speed

            # 時間が経過したら戻って残機表示
            if self._jump_time >= 190:
                return True

            self.bg_update()
            if not self._inGoal_tower:
                self.player.update(self._direction(self._img_number))

        return False

    # 土管に入る時のアニメーション
    def dokan_animation(self):
        if self.player.dive_dokan is not None:
            # 初期化
            if self._dokan_init:
                self._dokan_init = False
                Sound.play_SE('dokan')

                self.player.x_speed = 0.0
                SpritePlayer.scroll = 0

            # 一秒後に土管の処理を実行
            if self._dokan_count >= 60:
                if self.player.dive_dokan.data == 20.2:
                    if self._fly_dokan is None:
                        self._fly_dokan = Block.FlyDokan(self.player)
                    self._fly_dokan.update()
            else:
                self._dokan_count += 1
                self.player.y += 1

            self.bg_update()
            self.player.update(self._direction(self._img_number))

        return False

    # ゴール時のアニメーション
    def goal_animation(self):
        if not (self.player.isDeath or self.player.goal is None):
            # 初期化
            if self._goal_init:
                self._goal_init = False
                Sound.stop_BGM()
                Sound.play_SE('goal')
                self._goal_count = 0

                # プレイヤー座標のセット
                self.player.x_speed = self.player.y_speed = 0
                self.player.x = self.player.goal.rect.left - self.player.width + 7

                # ポール下の地面の座標を格納
                goal_block_list = [block for block in Stage.block_object_list if block.data == 7]
                for block in goal_block_list:
                    if block.rect.left == self.player.goal.rect.left - 3:
                        self._goal_scene_y = block.rect.top - 1

            # 一定の時間が経過したら次の面へ
            self._goal_count += 1
            if self._goal_count > 400:
                return True

            # ゴール塔に入った場合
            if self._inGoal_tower:
                self.bg_update()

            # 強制移動中
            elif self.goal_isMove:
                self.player.x_speed = 1.5

            # ポール掴み中
            else:
                # 一定の時間が経過したら移動モード切り替え
                if self._goal_count > 100 and self._goal_scene_y != 500:
                    self.goal_isMove = True
                    self._goal_count = 0

                # 地面に着いたらそのまま停止
                if not self.player.rect.bottom > self._goal_scene_y:
                    self.player.y += 3

                    # 画面外に出たら死
                    if self.player.y > 450:
                        self.player.isDeath = True

                self.bg_update()
                self.player.update(self.player.img_right[2])
        return False

    # x方向の当たり判定
    def collision_x(self):
        x = self.player.x + self.player.x_speed
        y = self.player.y + self.player.y_speed

        # 移動先の座標と矩形を求める
        start_x = (x - SpritePlayer.scroll)
        start_y = y + SpritePlayer.FALL_ACCELERATION * 2 + 15
        end_x = self.player.width / 2
        end_y = self.player.height - 30

        new_rect_left = Rect(start_x, start_y, end_x, end_y)
        new_rect_right = Rect(start_x + end_x, start_y, end_x, end_y)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_left)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_right)

        for block in Stage.block_object_list:
            collide_right = new_rect_right.colliderect(block.rect)
            collide_left = new_rect_left.colliderect(block.rect)

            # 当たり判定に背景画像・隠しブロックを除く
            if block.name not in SpriteBlock.BG and not block.isHide:
                # pygame.draw.rect(self.screen, (255, 0, 0), block.rect)  # 当たり判定可視化 （デバック用）

                # 左にある場合
                if collide_left:
                    self.block_animation('SIDE', block)

                    if self.player.x != 2 + block.rect.left - self.player.width and not self.player.x_speed > 0:
                        self.player.x_speed = 0.0
                        SpritePlayer.scroll = 0
                        self.player.x = block.rect.right - 3

                # 右にある場合
                if collide_right:
                    self.block_animation('SIDE', block)

                    if self.player.x != block.rect.right - 3 and not self.player.x_speed < 0:
                        self.player.x_speed = 0.0
                        SpritePlayer.scroll = 0
                        self.player.x = 2 + block.rect.left - self.player.width

            # 背景画像のアニメーション
            elif collide_left or collide_right:
                self.block_animation(block=block)

    # y方向の当たり判定
    def collision_y(self):
        x = self.player.x + self.player.x_speed
        y = self.player.y + self.player.y_speed

        # 移動先の座標と矩形を求める
        start_x = x - SpritePlayer.scroll
        start_y = y + SpritePlayer.FALL_ACCELERATION * 2 + 4
        end_x = self.player.width
        end_y = self.player.height / 4

        new_rect_top = Rect(start_x + 10, self.player.y, end_x - 18, end_y + 5)
        new_rect_bottom = Rect(start_x + 4, start_y + end_y * 3, end_x - 8, end_y)
        new_rect_block = Rect(start_x + 1, start_y - 10, end_x - 2, end_y * 3)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_top)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_bottom)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_block)

        for block in Stage.block_object_list:
            collide_top = new_rect_top.colliderect(block.rect)
            collide_bottom = new_rect_bottom.colliderect(block.rect)
            collide_block = new_rect_block.colliderect(block.rect)

            if block.name not in SpriteBlock.BG and block not in self.jump_disable_list:
                # 叩けないブロック
                if collide_block and not block.isHide:
                    self.block_animation('TOP_BLOCK', block)

                # 上にある場合
                if collide_top and self.player.y_speed < -1 and not self.player.isGrounding:
                    if not block.isHide:
                        self.player.y_speed /= -3
                    self.block_animation('TOP', block)

                    self.player.y = block.rect.bottom
                    self.player.isJump = False
                    self._img_number = 2
                    return False

                # 下にある場合
                if collide_bottom and self.player.y_speed > 0 and not block.isHide:
                    self.block_animation('BOTTOM', block)
                    if block in self.jump_disable_list:
                        return False
                    elif self.player.x != block.rect.bottom:
                        self.player.y = block.rect.top - self.player.height + 1
                        if not block.isAnimation:
                            self.player.y_speed = 0.0
                    return True

            # 背景画像のアニメーション
            elif collide_top or collide_bottom:
                self.block_animation(block=block)

        self._img_number = 2
        return False

    # ブロックのアニメーション
    def block_animation(self, direction='', block=None):
        def add_block(function):
            self.item_animation_list.append(function)

        # 近づくとアニメーション開始
        if block is None:
            for block in Stage.block_object_list:
                # ジャンプするとビームを放つ
                if block.data == 9.3 and not block.isBeam and not self.player.isGrounding:
                    if block.rect.left - self.player.rect.left < 82:
                        if block.y - self.player.y > -10:
                            block.isHide = False
                            block.isBeam = True
                            add_block(Block.Beam(block))
                            Text.set(self.screen, 'ビーー', sprite=block, tweak_x=10)

                # 近づくと落ちるブロック
                if block.data == 1.3 and not block.isAnimation:
                    if block.rect.left - self.player.rect.left < 0:
                        if block.rect.bottom - self.player.rect.bottom < 0:
                            add_block(Block.NearFall(block))

                # 近づくと敵出現イベント発生
                if block.data == 39 and not block.isAnimation:
                    if block.rect.left - self.player.rect.left < 25:
                        if self.player.rect.left - block.rect.left < 40:
                            add_block(Block.EventEnemy(block))

        # 当たるとアニメーション開始
        else:
            # 壊れるブロック
            if block.name == 'block1':
                # 近づくと落ちるブロックの当たり判定
                if block.data == 1.3 and block.isAnimation and direction == 'TOP_BLOCK':
                    self.player.isDeath = True

                if direction == 'TOP':
                    # 叩くと壊れる
                    if block.data == 1:
                        add_block(Block.Break(self.screen, block))

                    # 叩くと大量のコインが出る
                    if block.data == 1.6:
                        add_block(Block.Coin(self.screen, block, isLot=True))

                    # 叩くとPスイッチ
                    if block.data == 2.2:
                        Sound.play_SE('brockkinoko')

                        # ブロックデータの置き換え
                        block.name = 'block3'
                        block.data = 5
                        block.image = LoadImage.image_list[block.name]

                        # Pスイッチを表示
                        for p in Stage.block_object_list:
                            if p.data == 2.2 and block.x == p.x:
                                p.isHide = False

            # はてなブロック
            if block.name == 'block2':
                # 叩くとコイン
                if direction == 'TOP' and block.data == 3:
                    add_block(Block.Coin(self.screen, block))

                # 叩けないブロック
                if direction == 'TOP_BLOCK' and block.data == 3.1 and self.player.y_speed < 0:
                    block.rect.bottom = self.player.rect.top - 10

            # 隠しブロック
            if block.name == 'block3' and direction == 'TOP' and block.isHide:
                block.isHide = False

                # 叩くとコイン
                if block.data in [5, 5.1]:
                    add_block(Block.Coin(self.screen, block))

            # 針
            if block.name == 'block7' and direction == 'TOP':
                self.player.isDeath = True
                Text.set(self.screen, '刺さった!!', sprite=self.player)

            # 叩くアニメーション
            if direction == 'TOP':
                # 赤キノコ
                if block.data in [1.7, 3.2, 5.2]:
                    add_block(Block.Kinoko(self.screen, block))

                # 毒キノコ
                if block.data in [1.9, 3.4, 5.4]:
                    add_block(Block.PoisonKinoko(self.screen, block))

                # 大量の毒キノコ
                if block.data in [3.5, 5.5]:
                    add_block(Block.PoisonKinoko(self.screen, block, isLot=True))

                # まるい敵
                if block.data in [2.3, 3.8, 5.8]:
                    add_block(Block.Enemy(self.screen, block, 'enemy'))

                # 甲羅敵
                if block.data in [2.4, 3.9, 5.9]:
                    add_block(Block.Enemy(self.screen, block, 'koura1', tweak=10))

                # スター
                if block.data in [2.1, 3.7, 5.7]:
                    add_block(Block.Star(self.screen, block))

            # 乗ると壊れるブロック
            if direction == 'BOTTOM' and block.data in [1.4, 5.1]:
                add_block(Block.Break(self.screen, block))
                self.jump_disable_list.append(block)

            # コイン
            if block.name == 'item1':
                Sound.play_SE('coin')
                block.remove()
                Stage.block_object_list.remove(block)

            # トゲを生やす
            if block.data in [1.1, 7.1, 8.3]:
                block.isThorns = True
                self.player.isDeath = True
                Text.set(self.screen, 'シャキーン', sprite=block)

            # Pスイッチ
            if direction == 'BOTTOM' and block.name == 'block39' and not block.isHide:
                Sound.play_SE('Pswitch')
                Sound.stop_BGM()
                block.isHide = True
                self.jump_disable_list.append(block)

                # 全てコインに置き換え
                for b in Stage.block_object_list:
                    b.name = 'item1'
                    b.data = 25
                    b.image = LoadImage.image_list[b.name]

            # 土管に入る
            if block.name == 'dokan1':
                # 上から入る場合
                if direction == 'BOTTOM':
                    if block.data in [20.2, 20.3, 20.5] and block.rect.left + 25 < self.player.rect.right - 5:
                        if block.rect.right - 25 > self.player.rect.left + 6 and pygame.key.get_pressed()[K_DOWN]:
                            self.player.dive_dokan = block

                # 横からはいる場合
                if direction == 'SIDE' and block.data in [20.6, 20.8] and self.player.isGrounding:
                    pass

            # うめぇ
            if block.data == 19.2:
                self.player.isDeath = True
                block.name = 'cloud3'
                block.image = LoadImage.image_list[block.name]
                Text.set(self.screen, 'うめぇ!!', sprite=block)

            # 透明のうめぇ
            if block.data == 19.3:
                self.player.isDeath = True
                block.isHide = False
                Text.set(self.screen, 'うめぇ!!', sprite=block)

            # 乗ると落ちる足場ブロック
            if direction == 'BOTTOM' and block.data == 8.1 and not block.isAnimation:
                add_block(Block.RideFall())

            # ビームの当たり判定
            if block.name == 'beam' and not block.isHide and self.player.y + self.player.height > block.y + 25:
                self.player.isDeath = True

            # 中間地点
            if block.name == 'halfway' and not self.is_ai_mode:
                SpritePlayer.initial_x = 210
                SpritePlayer.initial_y = block.y
                SpritePlayer.initial_scroll_sum = block.x - 210

                block.remove()
                Stage.block_object_list.remove(block)

            # ゴールポール
            if block.name == 'goal_pole':
                if block.data == 9.1 and not self.goal_isMove:
                    self.player.goal = block

            # ゴール塔
            if block.name == 'end' and self.goal_isMove:
                start_x = block.x - SpritePlayer.scroll_sum + 60
                start_y = block.rect.top + 45
                end_x = block.width - 80
                end_y = block.height - 45
                block_rect = Rect(start_x, start_y, end_x, end_y)
                player_rect = Rect(self.player.x, self.player.y, self.player.width, self.player.height)

                # ゴール塔の中に入る
                if player_rect.colliderect(block_rect):
                    self._inGoal_tower = True
                    self._goal_init = False
                    self.goal_isMove = False
