import pygame
from Image import LoadImage, SpritePlayer


class BlockCoin:
    def __init__(self, screen, block):
        self.screen = screen

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
        pygame.draw.circle(self.screen, (0, 0, 0), (round(x), round(y)), 10)
        pygame.draw.circle(self.screen, (135, 95, 45), (round(x), round(y)), 9)