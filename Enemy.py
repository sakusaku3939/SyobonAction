import pygame
from pygame.locals import *

from Image import LoadImage


class Enemy(pygame.sprite.Sprite):
    def __init__(self, screen, stage):
        pygame.sprite.Sprite.__init__(self)

        self.screen = screen
        self.stage = stage
        self.x_speed = self.y_speed = 0.0

        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']  # 当たり判定を行わない背景画像
        self.rect_size_x = 7  # x方向の当たり判定の大きさ
        self.rect_size_y = 5  # y方向の当たり判定の大きさ

        self._enemy_init()

        self.player_x = 0
        self.player_y = 0

    def _enemy_init(self):
        for image in self.stage.enemy_object_list:
            print(image.name)
            # @TODO 敵の描画処理を追加

    def update(self):
        # @TODO 敵の歩行処理を追加
        pass

    # x方向の当たり判定
    def collision_x(self):
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

        for block in self.stage.image_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
                # 右にあるブロック
                if self.x_speed > 0.0:
                    self.player_x = block.rect.left - width
                    self.x_speed = 0.0
                    self.scroll = 0
                    return True

                # 左にあるブロック
                elif self.x_speed < 0.0:
                    self.player_x = block.rect.right - self.rect_size_x
                    self.x_speed = 0.0
                    self.scroll = 0
                    return True

        return False

    # y方向の当たり判定
    def collision_y(self):
        if self.y_speed == 0:
            return False

        width = self.rect.width
        height = self.rect.height

        # 移動先の座標と矩形を求める
        start_x = self.player_x + self.rect_size_x
        start_y = (self.player_y + self.y_speed + self.FALL_ACCELERATION * 2) + self.rect_size_y
        end_x = width - self.rect_size_x
        end_y = height - self.rect_size_y

        new_rect = Rect(start_x, start_y, end_x, end_y)

        for block in self.stage.image_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
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