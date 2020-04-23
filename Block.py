import pygame
from abc import ABCMeta, abstractmethod

from Enemy import Round
from Image import LoadImage
from Sound import Sound
from Sprite import SpritePlayer, SpriteObject
from Stage import Stage
from Text import Text


# ブロックから出現するスプライトを実装する際に継承するクラス
class AbstractBlock(metaclass=ABCMeta):
    def __init__(self, screen, block, img_name, isLot=False):
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
        self._isLot = isLot  # 大量に出現させるか
        self.isGenerate = False  # 新たに生成するか

        self.sprite = SpriteObject(screen, img_name, -30, -30)

        self.sprite.direction = -1  # アイテムが動く向き
        self.list_number = -1  # 画像の切り替え

        self.sprite.x_speed += 0.5 if isLot else 0  # 移動速度

        # オブジェクトの座標
        self.sprite.x = block.rect.left + int(block.width / 2 - self.sprite.width / 2) + SpritePlayer.scroll_sum
        self.sprite.rect.top = block.rect.top + 2
        self.start_y = self.sprite.rect.top

    @abstractmethod
    def update(self):
        if self.isAppear:
            self.move_animation()
        else:
            self.appear_animation()

        # 画面外になったらスプライト削除
        if self.sprite.isRemove:
            self.sprite.remove()
            self.isSuccess = True

    @abstractmethod  # ブロックから出現後の移動アニメーション
    def move_animation(self):
        self.sprite.update(self.list_number)

        # ブロックとの当たり判定
        self.sprite.collision(Stage.block_object_list)

        # プレイヤーとの当たり判定
        collision_x, collision_y = self.sprite.sprite_collision(self.player)
        collision_y(self.collision, self.collision)

    # ブロックから出現するアニメーション
    def appear_animation(self):
        # 一定の高さまで上がったら出現アニメーション完了
        if self.start_y - self.sprite.rect.top >= 29:
            self.isAppear = True
            self.isGenerate = self._isLot

        self.sprite.rect.left = self.sprite.x - SpritePlayer.scroll_sum
        self.sprite.rect.top -= 1

        # 向きによって画像を変更
        if self.list_number == -1:
            self.screen.blit(self.sprite.img_left[self.list_number], self.sprite.rect)
        else:
            self.screen.blit(self.sprite.img_right[self.list_number], self.sprite.rect)

    # プレイヤーに当たった場合
    def collision(self):
        self.isSuccess = True


# 叩くと赤キノコ
class Kinoko(AbstractBlock):
    def __init__(self, screen, block):
        super().__init__(screen, block, 'item2')

    def update(self):
        super().update()

    def move_animation(self):
        super().move_animation()

    def collision(self):
        super().collision()
        Sound.play_SE('powerup')
        Text.set(self.screen, 'まずい…', sprite=self.player)


# 叩くと毒キノコ
class PoisonKinoko(AbstractBlock):
    def __init__(self, screen, block, isLot=False):
        super().__init__(screen, block, 'item4', isLot)

    def update(self):
        super().update()

    def move_animation(self):
        super().move_animation()

    def collision(self):
        super().collision()
        self.player.isDeath = True
        Text.set(self.screen, 'うほっ!!!!', sprite=self.player)


# 叩くと敵
class Enemy(AbstractBlock):
    def __init__(self, screen, block, name):
        super().__init__(screen, block, name)

        self.sprite.direction = -1
        self.list_number = 0
        self.sprite.x -= 2

    def update(self):
        super().update()

    def move_animation(self):
        self.sprite.specific = Round(self.screen, self.player, self.sprite)
        Stage.enemy_object_list.append(self.sprite)

        self.isSuccess = True
        self.sprite.remove()


# 叩くとコイン
class Coin:
    def __init__(self, screen, block):
        Sound.play_SE('coin')
        self.screen = screen

        # ブロックデータの置き換え
        block.name = 'block3'
        block.data = 5
        block.image = LoadImage.image_list[block.name]

        self.isSuccess = False  # アニメーションが完了したかどうか
        self.isGenerate = False  # 新たに生成するか

        # 画像の読み込み
        self.image = LoadImage.image_list['item1']

        # コインの座標
        self.x = block.rect.left + int(block.width / 2 - self.image.get_width() / 2)
        self.y = block.rect.top - 8
        self.start_y = self.y

    def update(self):
        self.x -= SpritePlayer.scroll
        self.y -= 3
        self.screen.blit(self.image, (self.x, self.y))

        # 一定の高さまで上がったらアニメーション完了
        if self.start_y - self.y > 72:
            self.isSuccess = True


# 叩くと壊れる
class Break:
    def __init__(self, screen, block):
        Sound.play_SE('brockbreak')
        self.screen = screen

        self.isSuccess = False  # アニメーションが完了したかどうか
        self.isGenerate = False  # 新たに生成するか
        self.FALL_ACCELERATION = 0.5  # 落下加速度

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
        self.y_top_speed -= self.FALL_ACCELERATION
        self.y_top -= self.y_top_speed
        self.y_bottom_speed -= self.FALL_ACCELERATION
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