from abc import ABCMeta, abstractmethod
import pygame
from pygame.locals import *

from Sound import Sound
from Stage import Stage
from Text import Text


class Enemy:
    def __init__(self, screen):
        self.screen = screen
        self.player = Stage.player_object

        # 敵固有の設定
        self.specific_settings()

    def update(self):
        for enemy in Stage.enemy_object_list:
            enemy.update(enemy.specific.list_number)

            # 画面内の領域のみ処理
            if enemy.isDraw:
                # ブロックとの当たり判定
                if enemy.isPhysics:
                    enemy.collision(Stage.block_object_list)

                # プレイヤーとの当たり判定
                player_collision_x, player_collision_y = enemy.sprite_collision(self.player)

                # 死亡アニメーション時は戻る
                if not self.player.isDeath:
                    if not player_collision_x(enemy.specific.side_collision):
                        player_collision_y(enemy.specific.top_collision, enemy.specific.bottom_collision)

                # 敵固有の動作
                enemy.specific.update()

            # 画面外になったらオブジェクト削除
            if enemy.isRemove:
                enemy.remove()
                Stage.enemy_object_list.remove(enemy)

    def specific_settings(self):
        for enemy in Stage.enemy_object_list:
            if enemy.name == "enemy":
                enemy.specific = Round(self.screen, self.player, enemy)

            elif enemy.name == 'koura1':
                enemy.specific = Koura(self.screen, self.player, enemy)

            elif enemy.name == 'fish1' or enemy.name == 'fish2':
                enemy.specific = Fish(self.screen, self.player, enemy)

            else:
                enemy.specific = Round(self.screen, self.player, enemy)


# 敵を実装する際に継承するクラス
class AbstractEnemy(metaclass=ABCMeta):
    def __init__(self, screen, player, enemy, kill_text):
        self.screen = screen
        self.player = player
        self.enemy = enemy

        self.kill_text = kill_text  # プレイヤーを倒した時に放つ言葉
        self.list_number = 0  # 画像が複数枚ある場合の切り替え

    @abstractmethod  # 敵独自の動き
    def update(self):
        pass

    @abstractmethod  # プレイヤーの上に当たった場合
    def top_collision(self):
        pass

    @abstractmethod  # プレイヤーの下に当たった（踏まれた）場合
    def bottom_collision(self):
        pass

    @abstractmethod  # プレイヤーの横に当たった場合
    def side_collision(self):
        pass

    def kill(self):
        self.player.isDeath = True
        Text.set(self.screen, self.kill_text, sprite=self.enemy)


# まるい敵
class Round(AbstractEnemy):
    def __init__(self, screen, player, enemy):
        kill_text = [
            "遅すぎるんだよ!!",
            "無駄無駄無駄無駄ァ!!",
            "テラヨワス",
            "ぷー クスクス",
            "強靭!!無敵!!最強!!!!",
            "性能の差だな…",
            "カエレ!!",
            "ニマニマ"
        ]
        super().__init__(screen, player, enemy, kill_text)

    def update(self):
        pass

    def top_collision(self):
        super().kill()

    def bottom_collision(self):
        # 踏めない敵
        if self.enemy.data == 27.1:
            Sound.play_SE('humi')

            # 踏んだ勢いでジャンプ
            self.player.y_speed = self.player.JUMP_SPEED - 4.3
            self.player.limit_air_speed()

        # 踏める敵
        else:
            Sound.play_SE('humi')

            # 踏まれたら消える
            self.enemy.remove()
            Stage.enemy_object_list.remove(self.enemy)

            # 踏んだ勢いでジャンプ
            self.player.isGrounding = True
            self.player.isJump = True
            self.player.y_speed = self.player.JUMP_SPEED + 0.5
            self.player.limit_air_speed()

    def side_collision(self):
        super().kill()


# 甲羅亀
class Koura(AbstractEnemy):
    def __init__(self, screen, player, enemy):
        kill_text = "鉄壁!!よって、無敵!!"
        enemy.direction = -1

        super().__init__(screen, player, enemy, kill_text)

    def update(self):
        for other_enemy in Stage.enemy_object_list:
            if other_enemy.isDraw and other_enemy != self.enemy:
                # 甲羅が他の敵に当たった時はそのまま倒す
                if self.list_number == 1 and self.enemy.direction != 0:
                    def _remove():
                        Sound.play_SE('koura')
                        other_enemy.remove()
                        Stage.enemy_object_list.remove(other_enemy)

                    enemy_collision_x, enemy_collision_y = self.enemy.sprite_collision(other_enemy)
                    enemy_collision_x(_remove)

    def top_collision(self):
        super().kill()

    def bottom_collision(self):
        Sound.play_SE('humi')

        # 甲羅になる場合
        if self.list_number == 0:
            self.list_number = 1
            self.kill_text = "ざまぁｗ"

            self.enemy.direction = 0
            self.enemy.x += 4
            self.enemy.x_speed = 4.0
            self.enemy.width = self.enemy.img_left[self.list_number].get_width()
            self.enemy.height = self.enemy.img_left[self.list_number].get_height()

        # 甲羅を蹴る場合
        elif self.list_number == 1:
            if self.enemy.direction == 0:
                self.kick_koura()
            elif not self.player.isDeath:
                self.enemy.direction = 0

        # 踏んだ勢いでジャンプ
        self.player.isGrounding = True
        self.player.isJump = True
        self.player.y_speed = self.player.JUMP_SPEED + 1
        self.player.limit_air_speed()

    def side_collision(self):
        # 甲羅が止まっている場合はそのまま蹴る
        if self.list_number == 1 and self.enemy.direction == 0:
            self.kick_koura()
        else:
            self.player.isDeath = True
            Text.set(self.screen, self.kill_text, sprite=self.enemy)

    # 甲羅を蹴った時の動作
    def kick_koura(self):
        if self.player.x > self.enemy.rect.left:
            self.enemy.direction = 1
            self.enemy.x -= 3
        else:
            self.enemy.direction = -1
            self.enemy.x += 3


# 飛ぶ魚
class Fish(AbstractEnemy):
    def __init__(self, screen, player, enemy):
        kill_text = "Zzz"
        enemy.isPhysics = False
        enemy.direction = 0
        super().__init__(screen, player, enemy, kill_text)

        self.isAnimation = False
        self.y_speed = 6

        # 上向き
        if enemy.name == 'fish1':
            self.direction = -1
            enemy.rect.top = 480
            self.isDive_dokan = self._isDokan()
        # 下向き
        else:
            self.direction = 1
            enemy.rect.top = -45
            self.isDive_dokan = False

    # 下に土管がある場合は土管から出る
    def _isDokan(self):
        start_x = self.enemy.rect.left
        start_y = self.enemy.y + self.enemy.height / 3 + 15
        end_x = self.enemy.width
        end_y = self.enemy.height / 3

        new_rect = Rect(start_x, start_y, end_x, end_y)
        # pygame.draw.rect(self.screen, (0, 0, 255), new_rect)  # 当たり判定可視化 （デバック用）

        for block in Stage.block_object_list:
            collide = new_rect.colliderect(block.rect)

            if collide and block.name == 'dokan1':
                self.y_speed = 4
                self.enemy.x += 10
                self.enemy.rect.top = block.rect.bottom + 11
                return True
        return False

    def update(self):
        if not self.isAnimation:
            self.animation_start()

        if self.isAnimation:
            self.enemy.rect.top += self.y_speed * self.direction

    # アニメーションのスタート
    def animation_start(self):
        distance = 37 if self.isDive_dokan else 90

        if self.enemy.rect.left > 0 and self.enemy.rect.left - self.player.x < distance:
            Sound.play_SE('kirra')
            self.isAnimation = True

    def top_collision(self):
        super().kill()

    def bottom_collision(self):
        super().kill()

    def side_collision(self):
        super().kill()
