import pygame
from pygame.locals import *

from Sound import Sound
from Stage import Stage


class Enemy:
    def __init__(self, screen):
        self.screen = screen
        self.sprite = Stage.player_object
        self.enemy = None

        self.FALL_ACCELERATION = 0.27  # 落下加速度

    def update(self):
        for enemy in Stage.enemy_object_list:
            self.enemy = enemy
            enemy.update()

            # 画面内の領域のみ処理
            if enemy.isDraw:
                # ブロックとの当たり判定
                enemy.collision(Stage.block_object_list)

                # プレイヤーとの当たり判定
                collision_x, collision_y = enemy.sprite_collision(self.sprite)

                # 死亡アニメーション時は戻る
                death = not self.sprite.isDeath
                if death:
                    if death and not collision_y(self._top_collision, self._bottom_collision):
                        collision_x(self._side_collision)

            # 画面外になったらオブジェクト削除
            if enemy.isRemove:
                enemy.remove()
                Stage.enemy_object_list.remove(enemy)

    def _top_collision(self):
        self.sprite.isDeath = True

    def _bottom_collision(self):
        Sound.play_SE('humi')
        self.enemy.remove()
        Stage.enemy_object_list.remove(self.enemy)

        self.sprite.isGrounding = True
        self.sprite.isJump = True
        self.sprite.y_speed = self.sprite.JUMP_SPEED
        self.sprite.limit_air_speed()

    def _side_collision(self):
        self.sprite.isDeath = True
