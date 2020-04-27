import pygame
from abc import ABCMeta, abstractmethod

from Enemy import Round
from Image import LoadImage
from Sound import Sound
from Sprite import SpritePlayer, SpriteObject
from Stage import Stage
from Text import Text


# ブロック固有のアニメーションを実装する際に継承するクラス
class AbstractBlock(metaclass=ABCMeta):
    def __init__(self):
        self.isSuccess = False  # アニメーションが完了したかどうか
        self.isGenerate = False  # 新たに生成するか

    @abstractmethod
    def update(self):
        pass


# 叩くとコイン
class Coin(AbstractBlock):
    generate_count = 0

    def __init__(self, screen, block, isLot=False):
        Sound.play_SE('coin')
        super().__init__()
        self.screen = screen
        self.block = block

        self.isLot = isLot  # 大量に生成させるか
        self.GENERATE_MAX = 20  # 生成する個数

        # ブロックデータの置き換え
        block.name = 'block3'
        block.data = 5
        block.image = LoadImage.image_list[block.name]

        # 画像の読み込み
        self.image = LoadImage.image_list['item1']

        # コインの座標
        self.x = self.block.x - SpritePlayer.scroll_sum
        self.y = block.rect.top - 8
        self.start_y = self.y
        self.y_speed = 4.0

    def update(self):
        # 大量に出現させる場合、新たにコインを生成
        if self.isLot and self.start_y - self.y > 20:
            self.isLot = False
            self.isGenerate = True

        # 一定の高さまで上がったらアニメーション完了
        if self.start_y - self.y > 70:
            self.isSuccess = True

        self.x = self.block.x - SpritePlayer.scroll_sum
        self.y -= self.y_speed
        self.y_speed -= 0.1
        self.screen.blit(self.image, (self.x, round(self.y)))


# 叩くと壊れる
class Break(AbstractBlock):
    def __init__(self, screen, block):
        Sound.play_SE('brockbreak')
        super().__init__()
        self.screen = screen

        self.SPECIFIC_FALL_ACCELERATION = 0.5  # 落下加速度

        # 破壊ブロックの座標
        self.x = block.rect.left + int(block.width / 2)
        self.y_top = block.rect.top
        self.y_bottom = block.rect.top + 5

        # 速度
        self.x_top_speed = self.x_bottom_speed = 0.0
        self.y_top_speed = 8.0
        self.y_bottom_speed = self.y_top_speed - 1.0

    def update(self):
        # x方向の速度
        self.x -= SpritePlayer.scroll
        self.x_top_speed += 1.2
        self.x_bottom_speed += 1.4

        # y方向の速度
        self.y_top_speed -= self.SPECIFIC_FALL_ACCELERATION
        self.y_top -= self.y_top_speed
        self.y_bottom_speed -= self.SPECIFIC_FALL_ACCELERATION
        self.y_bottom -= self.y_bottom_speed

        # 破壊ブロックの描画
        self.draw_circle(self.x + 4 + self.x_bottom_speed, self.y_bottom)
        self.draw_circle(self.x - 4 - self.x_bottom_speed, self.y_bottom)
        self.draw_circle(self.x + 3 + self.x_top_speed, self.y_top)
        self.draw_circle(self.x - 3 - self.x_top_speed, self.y_top)

        # 画面外まで行ったらアニメーション完了
        if self.y_top > 500:
            self.isSuccess = True

    def draw_circle(self, x, y):
        pygame.draw.circle(self.screen, (0, 0, 0), (int(x), int(y)), 10)
        pygame.draw.circle(self.screen, (135, 95, 45), (int(x), int(y)), 9)


# 乗ると落ちるブロック
class RideFall(AbstractBlock):
    def __init__(self):
        super().__init__()
        self.player = Stage.player_object
        self.y = self.y_speed = 0
        self.block_list = []

        start_x = end_x = 0

        # プレイヤーに近いブロックグループを落下させる
        for block in [b for b in Stage.block_object_list if b.data == 8.1]:
            if block.group == 'start':
                start_x = block.rect.left - block.width
            if block.group == 'end':
                end_x = block.rect.left + 3

            if start_x != 0:
                self.block_list.append(block)

            if end_x != 0:
                if start_x < self.player.rect.left < end_x:
                    break
                else:
                    start_x = end_x = 0
                    self.block_list = []

    def update(self):
        # 落下アニメーション
        self.y_speed += SpritePlayer.FALL_ACCELERATION

        for block in self.block_list:
            block.isAnimation = True
            block.y += self.y_speed
            block.rect.top = block.y + 1

            # 画面外まで行ったらアニメーション完了
            if block.rect.top > 600:
                self.isSuccess = True
                block.isAnimation = False


# 近づくと落ちるブロック
class NearFall(AbstractBlock):
    def __init__(self, block_data):
        super().__init__()
        self.player = Stage.player_object
        self.block = block_data
        self.block_list = []
        self.y_speed = 0
        self.previous_y = 0

        # ブロックのグループ化
        for block in [b for b in Stage.block_object_list if b.data == 1.3]:
            self.block_list.append(block)
            if block.group == 'end':
                if block_data in self.block_list:
                    break
                else:
                    self.block_list = []

    def update(self):
        # 死亡アニメーション中は落下アニメーション停止
        if self.player.isDeath:
            for block in self.block_list:
                block.rect.top = block.y + 20
        else:
            self.y_speed += SpritePlayer.FALL_ACCELERATION

            for block in self.block_list:
                block.isAnimation = True
                block.y += self.y_speed
                block.rect.top = block.y

                # 画面外まで行ったらアニメーション完了
                if block.rect.top > 600:
                    self.isSuccess = True
                    block.isAnimation = False


# 近づいてジャンプするとビームを放つ
class Beam(AbstractBlock):
    instance = False

    def __init__(self, block):
        super().__init__()
        Beam.instance = True
        self.block = block

    def update(self):
        self.block.x -= 8

        # 画面外まで行ったらアニメーション完了
        if self.block.rect.left < -150:
            self.isSuccess = True


# 近づくと敵出現イベント発生
class EventEnemy(AbstractBlock):
    def __init__(self, block):
        super().__init__()
        self.block = block
        block.isAnimation = True

        _event_enemy_number = [27.2]  # 敵イベントのExcel番号
        self.enemy_list = []  # イベントを適用する敵リスト

        # 範囲内のイベント敵をリストに追加
        for enemy in Stage.enemy_object_list:
            if enemy.data in _event_enemy_number:
                if block.x - 210 < enemy.x < block.x + 210:
                    self.enemy_list.append(enemy)

        # 初期設定
        for enemy in self.enemy_list:
            enemy.rect.bottom = 0
            enemy.x -= 1
            enemy.y_speed += 0.5
            enemy.direction = 0

    def update(self):
        for enemy in self.enemy_list:
            enemy.isDraw = True

            # 地面につくまでは前進しない
            if enemy.isGrounding:
                enemy.direction = 1
                enemy.isEvent = False


# ブロックから出現するスプライトを実装する際に継承するクラス
class AbstractSpriteAppear(metaclass=ABCMeta):
    def __init__(self, screen, block, img_name, data=0):
        Sound.play_SE('brockkinoko')
        self.screen = screen
        self.block = block
        self.player = Stage.player_object

        # ブロックデータの置き換え
        block.name = 'block3'
        block.data = 5
        block.image = LoadImage.image_list[block.name]

        self.isSuccess = False  # アニメーションが完了したかどうか
        self.isAppear = False  # 出現アニメーション中か
        self.isGenerate = False  # 新たに生成するか

        self.sprite = SpriteObject(screen, img_name, data, -30, -30)

        self.sprite.direction = -1  # アイテムが動く向き
        self.list_number = -1  # 画像の切り替え

        # オブジェクトの座標
        self.sprite.x = block.rect.left + int(block.width / 2 - self.sprite.width / 2) + SpritePlayer.scroll_sum
        self.sprite.rect.top = block.rect.top + 2
        self.start_y = self.sprite.rect.top

        # 描画範囲
        self.START_RANGE_X = -50

    def update(self):
        if self.isAppear:
            self.move_animation()
        else:
            self.appear_animation()

        # 画面外になったらスプライト削除
        if self.sprite.x - SpritePlayer.scroll_sum < self.START_RANGE_X \
                or not self.sprite.START_RANGE_Y < self.sprite.rect.top < self.sprite.END_RANGE_Y:
            self.sprite.remove()
            self.isSuccess = True

    # ブロックから出現するアニメーション
    def appear_animation(self):
        # 一定の高さまで上がったら出現アニメーション完了
        if self.start_y - self.sprite.rect.top >= 29:
            self.isAppear = True

        self.sprite.rect.left = self.sprite.x - SpritePlayer.scroll_sum
        self.sprite.rect.top -= 1

        # 向きによって画像を変更
        if self.list_number == -1:
            self.screen.blit(self.sprite.img_left[self.list_number], self.sprite.rect)
        else:
            self.screen.blit(self.sprite.img_right[self.list_number], self.sprite.rect)

    @abstractmethod  # ブロックから出現後の移動アニメーション
    def move_animation(self):
        self.sprite.update(self.list_number)

        # ブロックとの当たり判定
        self.sprite.collision(Stage.block_object_list)

        # プレイヤーとの当たり判定
        collision_x, collision_y = self.sprite.sprite_collision(self.player)
        collision_y(self.collision, self.collision)

    @abstractmethod  # プレイヤーに当たった場合
    def collision(self):
        self.isSuccess = True


# 叩くと赤キノコ
class Kinoko(AbstractSpriteAppear):
    def __init__(self, screen, block):
        super().__init__(screen, block, 'item2')

    def move_animation(self):
        super().move_animation()

    def collision(self):
        super().collision()
        Sound.play_SE('powerup')
        Text.set(self.screen, 'まずい…', sprite=self.player)


# 叩くと毒キノコ
class PoisonKinoko(AbstractSpriteAppear):
    generate_count = 0

    def __init__(self, screen, block, isLot=False):
        super().__init__(screen, block, 'item4')
        self.isLot = isLot  # 大量に生成させるか
        self.GENERATE_MAX = -1  # 生成する個数
        self.sprite.x_speed = 1.0 if isLot else 0.5  # 移動速度

    def move_animation(self):
        super().move_animation()

    def appear_animation(self):
        super().appear_animation()
        if self.isAppear:
            self.isGenerate = self.isLot

    def collision(self):
        super().collision()
        self.player.isDeath = True
        Text.set(self.screen, 'うほっ!!!!', sprite=self.player)


# 叩くとスター
class Star(AbstractSpriteAppear):
    def __init__(self, screen, block):
        super().__init__(screen, block, 'item5')
        self.sprite.x_speed = 0.83

    def move_animation(self):
        self.sprite.update(self.list_number)

        # ブロックとの当たり判定
        self.sprite.collision(Stage.block_object_list)

        # 地面に着いたらジャンプ
        if self.sprite.isGrounding:
            self.sprite.y_speed = -7

        # プレイヤーとの当たり判定
        collision_x, collision_y = self.sprite.sprite_collision(self.player)
        collision_y(self.collision, self.collision)

    def collision(self):
        super().collision()
        self.player.isDeath = True
        Text.set(self.screen, 'ぐふぅ!!', sprite=self.player)


# 叩くと敵
class Enemy(AbstractSpriteAppear):
    def __init__(self, screen, block, name):
        super().__init__(screen, block, name)

        self.sprite.direction = -1
        self.list_number = 0
        self.sprite.x -= 2

    def move_animation(self):
        self.sprite.specific = Round(self.screen, self.player, self.sprite)
        Stage.enemy_object_list.append(self.sprite)

        self.isSuccess = True
        self.sprite.remove()

    def collision(self):
        pass


# 入ると揺れて飛んでいく土管
class FlyDokan:
    def __init__(self, player):
        self.player = player
        self.player_y = float(self.player.y)

        self.x_speed = self.y_speed = 0.0
        self.direction = 1
        self.count = -40

        self.isFly = False

        # 少し左にずれる
        for dokan in Stage.block_object_list:
            if dokan.data == 20.2:
                dokan.x -= 1
                self.player.x = dokan.x

    def update(self):
        self.count += 1

        # 画面外に出たら死
        if self.player_y < -900:
            self.player.isDeath = True

            self.y_speed = 0.0

        # ある程度まで揺れたら飛行開始
        if self.x_speed > 5:
            self.isFly = True
            self.count = -30
            self.x_speed = 0

        if self.count >= 0:
            # 飛行モード
            if self.isFly:
                self.y_speed += 0.2

            # 初期位置に戻す
            elif self.count == 0:
                self.x_speed = 1.0
                for dokan in Stage.block_object_list:
                    if dokan.data == 20.2:
                        dokan.x += 1

            # 揺れモード
            elif self.count % 2 == 0:
                self.direction *= -1
                self.x_speed += 0.1

        self.player_y -= self.y_speed
        self.player.y = self.player_y

        for dokan in Stage.block_object_list:
            if dokan.data == 20.2:
                dokan.x += self.x_speed * self.direction
                dokan.y -= self.y_speed
                dokan.rect.top = int(dokan.y)
        return
