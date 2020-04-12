import pygame
from pygame.locals import *

from Stage import Stage


class Enemy:
    def __init__(self, screen):
        self.screen = screen

        # プレイヤースプライトからデータ読み込み
        self.player = Stage.player_object

        # 当たり判定を行わない背景画像
        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']

        self.FALL_ACCELERATION = 0.27  # 落下加速度

    def update(self):
        for enemy in Stage.enemy_object_list:
            if enemy.rect.left < 550:
                # 当たり判定
                sign = self.collision_x(enemy)
                self.collision_y(enemy)

                self.player_collision_x(enemy)
                self.player_collision_y(enemy)

                enemy.x -= enemy.x_speed * sign
                enemy.y_speed += self.FALL_ACCELERATION
                enemy.y += enemy.y_speed

            enemy.update()

    # x方向の当たり判定
    def collision_x(self, enemy):
        # 移動先の座標と矩形を求める
        start_x = enemy.rect.left + enemy.x_speed - 1
        start_y = enemy.y + 10
        end_x = enemy.width
        end_y = enemy.height - 20

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect)  # 当たり判定可視化 （デバック用）

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)
            # 歩く先にブロックがある場合向きを変える
            if collide and block.name not in self.bg:
                enemy.direction *= -1
        return enemy.direction

    # y方向の当たり判定
    def collision_y(self, enemy):
        # 移動先の座標と矩形を求める
        start_x = enemy.rect.left + 1
        start_y = enemy.y + enemy.y_speed + self.FALL_ACCELERATION * 2
        end_x = enemy.width - 4
        end_y = enemy.height - 2

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect)  # 当たり判定可視化 （デバック用）

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)
            if collide and block.name not in self.bg:
                # 下にある場合
                if enemy.y_speed > 0.0:
                    enemy.y = block.rect.top - enemy.height + 2
                    enemy.y_speed = 0.0
                    return True

                # 上にある場合
                elif enemy.y_speed < 0.0:
                    enemy.y = block.rect.bottom
                    enemy.y_speed = 0.0
                    return False
        return False

    # プレイヤーとのx方向の当たり判定
    def player_collision_x(self, enemy):
        # 移動先の座標と矩形を求める
        start_x = self.player.rect.left + self.player.x_speed + 5
        start_y = self.player.y + self.FALL_ACCELERATION * 2 + 15
        end_x = self.player.width - 10
        end_y = self.player.height - 30

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (255, 0, 0), new_rect)  # 当たり判定可視化 （デバック用）

        collide = new_rect.colliderect(enemy.rect)
        if collide:
            self.player.x_speed = 0.0
            self.player.isDeath = True
            self.player.scroll = 0
            return

        return

    # プレイヤーとのy方向の当たり判定
    def player_collision_y(self, enemy):
        # 移動先の座標と矩形を求める
        start_x = self.player.x + 3
        start_y = self.player.y + self.player.y_speed + self.FALL_ACCELERATION * 2 + 2
        end_x = self.player.width - 6
        end_y = (self.player.height / 2) - 2

        new_rect_top = Rect(start_x, start_y, end_x, end_y)

        start_y += end_y
        new_rect_bottom = Rect(start_x, start_y, end_x, end_y)

        # 当たり判定可視化 （デバック用）
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_top)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_bottom)

        collide_top = new_rect_top.colliderect(enemy.rect)
        collide_bottom = new_rect_bottom.colliderect(enemy.rect)
        # プレイヤーの上から当たった場合
        if collide_top:
            self.player.x_speed = 0.0
            self.player.isDeath = True
            self.player.scroll = 0
            return

        # プレイヤーに踏まれた場合
        if collide_bottom and not self.player.isGrounding:
            enemy.remove()
            Stage.enemy_object_list.remove(enemy)

            self.player.isGrounding = True
            self.player.y_speed = self.player.JUMP_SPEED
            self.player.limit_air_speed()
            return

        return
