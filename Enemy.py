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

    def update(self):
        for enemy in Stage.enemy_object_list:
            if enemy.rect.left < 480:
                sign = self.collision_x(enemy)
                self.collision_y(enemy)

                # enemy.x -= enemy.x_speed * sign
                enemy.y_speed += self.FALL_ACCELERATION
                enemy.y += enemy.y_speed

            enemy.update()

    # x方向の当たり判定
    def collision_x(self, enemy):
        # 移動先の座標と矩形を求める
        start_x = enemy.rect.left + enemy.x_speed
        start_y = enemy.y + 10
        end_x = enemy.width
        end_y = enemy.height - 20

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect)  # 当たり判定可視化 （デバック用）

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
                enemy.direction *= -1
        return enemy.direction

    # y方向の当たり判定
    def collision_y(self, enemy):
        # 移動先の座標と矩形を求める
        start_x = enemy.rect.left + 2
        start_y = enemy.y + enemy.y_speed + self.FALL_ACCELERATION * 2
        end_x = enemy.width - 6
        end_y = enemy.height

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect)  # 当たり判定可視化 （デバック用）

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
                # 下にあるブロック
                if enemy.y_speed > 0.0:
                    enemy.y = block.rect.top - enemy.height
                    enemy.y_speed = 0.0
                    return True

                # 上にあるブロック
                elif enemy.y_speed < 0.0:
                    enemy.y = block.rect.bottom
                    enemy.y_speed = 0.0
                    return False
        return False
