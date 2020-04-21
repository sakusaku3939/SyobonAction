import pygame
from pygame.locals import *

from Sound import Sound
from Stage import Stage


class Enemy:
    def __init__(self, screen):
        self.screen = screen

        # プレイヤースプライトからデータ読み込み
        self.sprite = Stage.player_object

        self.FALL_ACCELERATION = 0.27  # 落下加速度

    def update(self):
        for enemy in Stage.enemy_object_list:
            # 画面内の領域のみ処理
            if enemy.isDraw:
                # プレイヤーとの当たり判定
                self.player_collision(enemy)

            enemy.update(Stage.block_object_list)

            # 画面外になったらオブジェクト削除
            if enemy.isRemove:
                enemy.remove()
                Stage.enemy_object_list.remove(enemy)

    # プレイヤーとの当たり判定
    def player_collision(self, enemy):
        def _player_collision_x():
            # 移動先の座標と矩形を求める
            start_x = self.sprite.rect.left + self.sprite.x_speed + 5
            start_y = self.sprite.y + self.FALL_ACCELERATION * 2 + 15
            end_x = self.sprite.width - 10
            end_y = self.sprite.height - 30

            new_rect = Rect(start_x, start_y, end_x, end_y)
            # pygame.draw.rect(self.screen, (255, 0, 0), new_rect)  # 当たり判定可視化 （デバック用）

            collide = new_rect.colliderect(enemy.rect)

            # プレイヤーの横から当たった場合
            if collide:
                self.sprite.isDeath = True
                return

        def _player_collision_y():
            # 移動先の座標と矩形を求める
            start_x = self.sprite.x + 2
            start_y = self.sprite.y + self.sprite.y_speed + self.FALL_ACCELERATION * 2 + 4
            end_x = self.sprite.width - 4
            end_y = (self.sprite.height / 2) - 2

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
                self.sprite.isDeath = True
                return True

            # プレイヤーに踏まれた場合
            if collide_bottom and not self.sprite.isGrounding:
                Sound.play_SE('humi')
                enemy.remove()
                Stage.enemy_object_list.remove(enemy)

                self.sprite.isGrounding = True
                self.sprite.isJump = True
                self.sprite.y_speed = self.sprite.JUMP_SPEED
                self.sprite.limit_air_speed()
                return True

            return False

        # 死亡アニメーション時は戻る
        death = not self.sprite.isDeath
        if death:
            if death and not _player_collision_y():
                _player_collision_x()
