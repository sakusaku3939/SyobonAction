import pygame
from Image import LoadImage
from Sound import Sound
from Sprite import SpritePlayer, SpriteObject
from Stage import Stage
from Text import Text


class BlockItem:
    def __init__(self, screen, block, item_name):
        Sound.play_SE('brockkinoko')
        self.screen = screen

        # ブロックデータの置き換え
        block.name = 'block3'
        block.data = 5
        block.image = LoadImage.image_list[block.name]

        self.isSuccess = False  # アニメーションが完了したかどうか
        self.isAppear = False  # アイテム出現アニメーション中か

        self.item = SpriteObject(screen, item_name, -30, -30)

        self.item.direction = -1  # アイテムが動く向き

        # アイテムの座標
        self.item.x = block.rect.left + int(block.width / 2 - self.item.width / 2) + SpritePlayer.scroll_sum
        self.item.rect.top = block.rect.top
        self.start_y = self.item.rect.top

    def update(self):
        # 一定の高さまで上がったらアイテム出現アニメーション完了
        if self.start_y - self.item.rect.top >= 29:
            self.isAppear = True

        # アイテム移動アニメーション
        if self.isAppear:
            self.item.update(list_number=-1)

            # ブロックとの当たり判定
            self.item.collision(Stage.block_object_list)

            # プレイヤーとの当たり判定
            collision_x, collision_y = self.item.sprite_collision(Stage.player_object)
            collision_y(self._collision, self._collision)
        else:
            self.item.rect.left = self.item.x - SpritePlayer.scroll_sum
            self.item.rect.top -= 1
            self.screen.blit(self.item.image, self.item.rect)

        # 画面外になったらオブジェクト削除
        if self.item.isRemove:
            self.item.remove()
            self.isSuccess = True

    def _collision(self):
        self.isSuccess = True
        Sound.play_SE('powerup')
        Text.set(self.screen, 'まずい…', sprite=Stage.player_object)


class BlockCoin:
    def __init__(self, screen, block):
        Sound.play_SE('coin')
        self.screen = screen

        # ブロックデータの置き換え
        block.name = 'block3'
        block.data = 5
        block.image = LoadImage.image_list[block.name]

        self.isSuccess = False  # アニメーションが完了したかどうか

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


class BlockBreak:
    def __init__(self, screen, block):
        Sound.play_SE('brockbreak')
        self.screen = screen

        self.isSuccess = False  # アニメーションが完了したかどうか
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