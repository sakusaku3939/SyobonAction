from Sound import Sound
from Stage import Stage
from Text import Text


class Enemy:
    def __init__(self, screen):
        self.screen = screen
        self.sprite = Stage.player_object

        self.specific_settings()

    def update(self):
        for enemy in Stage.enemy_object_list:
            enemy.update(enemy.object.list_number)

            # 画面内の領域のみ処理
            if enemy.isDraw:
                # ブロックとの当たり判定
                enemy.collision(Stage.block_object_list)

                # プレイヤーとの当たり判定
                sprite_collision_x, sprite_collision_y = enemy.sprite_collision(self.sprite)

                # 死亡アニメーション時は戻る
                if not self.sprite.isDeath:
                    if not sprite_collision_y(enemy.object.top_collision, enemy.object.bottom_collision):
                        sprite_collision_x(enemy.object.side_collision)

            # 画面外になったらオブジェクト削除
            if enemy.isRemove:
                enemy.remove()
                Stage.enemy_object_list.remove(enemy)

    # スプライト固有の設定
    def specific_settings(self):
        for enemy in Stage.enemy_object_list:
            if enemy.name == "enemy":
                enemy.object = RoundEnemy(self.screen, self.sprite, enemy)

            elif enemy.name == 'koura1':
                enemy.object = Koura(self.screen, self.sprite, enemy)


class RoundEnemy:
    def __init__(self, screen, sprite, enemy):
        self.screen = screen
        self.sprite = sprite
        self.enemy = enemy

        self.list_number = 0
        self.kill_text = [
            "遅すぎるんだよ!!",
            "無駄無駄無駄無駄ァ!!",
            "テラヨワス",
            "ぷー クスクス",
            "強靭!!無敵!!最強!!!!",
            "性能の差だな…",
            "カエレ!!",
            "ニマニマ"
        ]

    def top_collision(self):
        self.sprite.isDeath = True
        Text.set(self.screen, self.kill_text, sprite=self.enemy)

    def bottom_collision(self):
        Sound.play_SE('humi')

        # 踏まれたら消える
        self.enemy.remove()
        Stage.enemy_object_list.remove(self.enemy)

        # 踏んだ勢いでジャンプ
        self.sprite.isGrounding = True
        self.sprite.isJump = True
        self.sprite.y_speed = self.sprite.JUMP_SPEED
        self.sprite.limit_air_speed()

    def side_collision(self):
        self.sprite.isDeath = True
        Text.set(self.screen, self.kill_text, sprite=self.enemy)


class Koura:
    def __init__(self, screen, sprite, enemy):
        self.screen = screen
        self.sprite = sprite
        self.enemy = enemy

        self.list_number = 0
        self.enemy.direction = -1
        self.kill_text = "鉄壁!!よって、無敵!!"

    def top_collision(self):
        self.sprite.isDeath = True
        Text.set(self.screen, self.kill_text, sprite=self.enemy)

    def bottom_collision(self):
        Sound.play_SE('humi')

        # 甲羅になる場合
        if self.list_number == 0:
            self.list_number = 1
            self.kill_text = "ざまぁｗ"

            self.enemy.direction = 0
            self.enemy.x += 3
            self.enemy.x_speed = 4.0
            self.enemy.width = self.enemy.img_left[self.list_number].get_width()
            self.enemy.height = self.enemy.img_left[self.list_number].get_height()

        # 甲羅を蹴る場合
        elif self.list_number == 1:
            if self.enemy.direction == 0:
                self.kick_koura()
            else:
                self.enemy.direction = 0

        # 踏んだ勢いでジャンプ
        self.sprite.isGrounding = True
        self.sprite.isJump = True
        self.sprite.y_speed = self.sprite.JUMP_SPEED
        self.sprite.limit_air_speed()

    def side_collision(self):
        if self.list_number == 1 and self.enemy.direction == 0:
            self.kick_koura()
        else:
            self.sprite.isDeath = True
            Text.set(self.screen, self.kill_text, sprite=self.enemy)

    def kick_koura(self):
        if self.sprite.x > self.enemy.rect.left:
            self.enemy.direction = 1
            self.enemy.x -= 3
        else:
            self.enemy.direction = -1
            self.enemy.x += 3

