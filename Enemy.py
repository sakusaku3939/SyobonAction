import pygame
from pygame.locals import *

from Stage import Stage


class Enemy(pygame.sprite.Sprite):
    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)

        self.screen = screen

        self.isGrounding = True  # 地面に着地しているか
        self.FALL_ACCELERATION = 0.27  # 落下加速度

        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']  # 当たり判定を行わない背景画像
        self.rect_size_x = 0  # x方向の当たり判定の大きさ
        self.rect_size_y = 0  # y方向の当たり判定の大きさ

    def update(self):
        for enemy in Stage.enemy_object_list:
            if enemy.rect.left < 480:
                self.collision_y(enemy)
                enemy.y_speed += self.FALL_ACCELERATION
                enemy.y += enemy.y_speed

                enemy.x -= enemy.x_speed

            enemy.update()

    # # x方向の当たり判定
    # def collision_x(self):
    #     if self.x_speed == 0:
    #         return False
    #
    #     width = self.rect.width
    #     height = self.rect.height
    #
    #     # 移動先の座標と矩形を求める
    #     start_x = (self.enemy_x + self.x_speed) + self.rect_size_x
    #     start_y = self.enemy_y + self.rect_size_y
    #     end_x = width - self.rect_size_x
    #     end_y = height - self.rect_size_y
    #
    #     new_rect = Rect(start_x, start_y, end_x, end_y)
    #
    #     for block in Stage.block_object_list:
    #         collide = new_rect.colliderect(block.rect)
    #         if collide and block.name not in self.bg:
    #             # 右にあるブロック
    #             if self.x_speed > 0.0:
    #                 self.enemy_x = block.rect.left - width
    #                 self.x_speed = 0.0
    #                 self.scroll = 0
    #                 return True
    #
    #             # 左にあるブロック
    #             elif self.x_speed < 0.0:
    #                 self.enemy_x = block.rect.right - self.rect_size_x
    #                 self.x_speed = 0.0
    #                 self.scroll = 0
    #                 return True
    #
    #     return False

    # y方向の当たり判定
    def collision_y(self, enemy):
        if enemy.y_speed == 0:
            return False

        width = enemy.rect.width
        height = enemy.rect.height

        # 移動先の座標と矩形を求める
        start_x = enemy.x + self.rect_size_x
        start_y = (enemy.y + enemy.y_speed + self.FALL_ACCELERATION * 2) + self.rect_size_y
        end_x = width - self.rect_size_x
        end_y = height - self.rect_size_y

        new_rect = Rect(start_x, start_y, end_x, end_y)

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
                # 下にあるブロック
                if enemy.y_speed > 0.0:
                    enemy.y = block.rect.top - height
                    enemy.y_speed = 0.0
                    return True

                # 上にあるブロック
                elif enemy.y_speed < 0.0:
                    enemy.y = block.rect.bottom
                    enemy.y_speed = 0.0
                    return False
        return False
