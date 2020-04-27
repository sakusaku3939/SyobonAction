import pygame
from pygame.locals import *

from Image import LoadImage


# 敵やアイテム等のスプライト
class SpriteObject(pygame.sprite.Sprite):
    def __init__(self, screen, img_name, data, x, y, tweak_x=0, tweak_y=0):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen
        self.specific = None  # スプライト固有の設定を入れるオブジェクト
        self.data = data  # 画像のExcel番号

        # 画像の読み込み
        self.name = img_name
        self.image = LoadImage.image_list[img_name]

        def _load_image():
            img = [self.image]

            # 画像が複数ある場合はリストに追加
            if "1" in self.name:
                for i in range(2, 5):
                    name = self.name[:-1] + str(i)
                    if name in LoadImage.image_list:
                        img.append(LoadImage.image_list[name])

            return img

        # 画像を格納
        self.img_left = _load_image()
        self.img_right = [pygame.transform.flip(img, True, False) for img in self.img_left]

        # 初期座標
        self.x = int(x * 29 + tweak_x)
        self.y = int(y * 29 - 12 + tweak_y)

        """ # 画面内での座標
        self.rect.left = self.x - SpritePlayer.scroll_sum
        self.rect.top = self.y
        """

        self.x_speed = 0.5  # 移動速度
        self.y_speed = 0.0  # 落下速度
        self.direction = 1  # 向き （1 or -1）
        self.isPhysics = True  # 物理演算を行うか

        self.isEvent = False  # イベントポイントによって出現するか
        self._event = False

        # スプライトのサイズ
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # 初期位置に描画
        self.rect = Rect(self.x - SpritePlayer.initial_scroll_sum, self.y, self.width, self.height)
        screen.blit(self.image, self.rect)

        self.isGrounding = False  # 地面に着地しているか

        # 描画する範囲
        self.START_RANGE_X = -100
        self.END_RANGE_X = 500
        self.START_RANGE_Y = -50
        self.END_RANGE_Y = 500
        self.isDraw = False
        self.isRemove = False

    def update(self, list_number=0):

        if self.x - SpritePlayer.scroll_sum < self.END_RANGE_X and not self.isEvent:
            self.isDraw = True

        if self.isDraw:
            # 描画位置を計算
            if self.direction != 0:
                self.x -= self.x_speed * self.direction
            self.y_speed += SpritePlayer.FALL_ACCELERATION if self.isPhysics else 0

            self.rect.left = self.x - SpritePlayer.scroll_sum
            self.rect.top += self.y_speed

            # 向きによって画像を変更
            if self.direction != -1 or list_number == -1:
                self.screen.blit(self.img_left[list_number], self.rect)
            else:
                self.screen.blit(self.img_right[list_number], self.rect)

        # 画面外になったらオブジェクト削除
        if self.x - SpritePlayer.scroll_sum < self.START_RANGE_X \
                or not self.START_RANGE_Y < self.rect.top < self.END_RANGE_Y:
            self.isRemove = True

    # ブロックとの当たり判定
    def collision(self, block_list):
        def _collision_x():
            # 移動先の座標と矩形を求める
            start_x = self.rect.left + self.x_speed - 2
            start_y = self.rect.top + 15
            end_x = (self.width + 4) / 2
            end_y = self.height - 20

            new_rect_left = Rect(start_x, start_y, end_x, end_y)

            start_x += end_x
            new_rect_right = Rect(start_x, start_y, end_x, end_y)

            # 当たり判定可視化 （デバック用）
            # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_left)
            # pygame.draw.rect(self.screen, (255, 0, 0), new_rect_right)

            for block in block_list:
                collide_left = new_rect_left.colliderect(block.rect)
                collide_right = new_rect_right.colliderect(block.rect)

                # 歩く先にブロックがある場合向きを変える
                if block.name not in SpriteBlock.BG:
                    if collide_left:
                        self.direction = -1
                    elif collide_right:
                        self.direction = 1

        def _collision_y():
            # 移動先の座標と矩形を求める
            start_x = self.rect.left + self.x_speed + 2
            start_y = self.rect.top + self.y_speed + SpritePlayer.FALL_ACCELERATION * 2
            end_x = self.width - 4
            end_y = (self.height - 2) / 2

            new_rect_top = Rect(start_x, start_y, end_x, end_y)

            start_y += end_y
            new_rect_bottom = Rect(start_x, start_y, end_x, end_y)

            # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_top)  # 当たり判定可視化 （デバック用）
            # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_bottom)  # 当たり判定可視化 （デバック用）

            for block in block_list:
                collide_top = new_rect_top.colliderect(block.rect)
                collide_bottom = new_rect_bottom.colliderect(block.rect)

                if block.name not in SpriteBlock.BG:
                    # 上にある場合
                    if collide_top:
                        self.rect.top = block.rect.bottom
                        self.y_speed /= -3
                        return False

                    # 下にある場合
                    elif collide_bottom:
                        self.rect.top = block.rect.top - self.height + 3
                        self.y_speed = 0.0
                        return True

            return False

        self.isGrounding = _collision_y()
        return _collision_x()

    # スプライトとの当たり判定
    def sprite_collision(self, sprite):
        def _sprite_collision_x(_side_function):
            # 移動先の座標と矩形を求める
            if sprite.name == 'player':
                start_x = sprite.rect.left + sprite.x_speed + 2
                start_y = sprite.y + SpritePlayer.FALL_ACCELERATION * 2 + 10
                end_x = sprite.width - 4
                end_y = sprite.height - 30
            else:
                start_x = sprite.rect.left + sprite.x_speed
                start_y = sprite.rect.top
                end_x = sprite.width
                end_y = sprite.height

            new_rect = Rect(start_x, start_y, end_x, end_y)

            # pygame.draw.rect(self.screen, (255, 0, 0), new_rect)  # 当たり判定可視化 （デバック用）

            collide = new_rect.colliderect(self.rect)

            # 横に当たった場合
            if collide:
                _side_function()
                return True
            return False

        def _sprite_collision_y(_top_function, _bottom_function):
            # 移動先の座標と矩形を求める
            start_x = sprite.rect.left + 4
            start_y = sprite.y + sprite.y_speed + SpritePlayer.FALL_ACCELERATION * 2 + 4
            end_x = sprite.width - 8
            end_y = (sprite.height / 3) - 2

            new_rect_top = Rect(start_x, start_y, end_x, end_y)

            start_x = sprite.rect.left + 4
            end_x = sprite.width - 8
            start_y += end_y + 6
            end_y += 6
            new_rect_bottom = Rect(start_x, start_y, end_x, end_y)

            # 当たり判定可視化 （デバック用）
            # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_top)
            # pygame.draw.rect(self.screen, (0, 0, 255), new_rect_bottom)

            collide_top = new_rect_top.colliderect(self.rect)
            collide_bottom = new_rect_bottom.colliderect(self.rect)

            # 上に当たった場合
            if collide_top:
                _top_function()
                return True

            # 下に当たった（踏まれた）場合
            if collide_bottom and not sprite.isGrounding:
                _bottom_function()
                return True

            return False

        return _sprite_collision_x, _sprite_collision_y


# ブロックのスプライト
class SpriteBlock(pygame.sprite.Sprite):
    # 当たり判定を行わない背景画像
    BG = ['bg', 'mountain', 'grass', 'cloud1', 'cloud2', 'cloud3',
          'cloud4', 'end', 'halfway', 'round', 'triangle', 'goal_pole', 'beam']

    def __init__(self, screen, img_name, data, x, y, tweak_x=0, tweak_y=0, group='', hide=False):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen

        self.data = data  # 画像のExcel番号
        self.isHide = hide  # 隠しスプライトかどうか
        self.isAnimation = False  # アニメーション中か
        self.group = group  # グループ化されている場合 "start" -> "end" が格納

        # 画像の読み込み
        self.name = img_name
        self.image = LoadImage.image_list[img_name]

        # ステージ全体での座標
        self.x = int(x * 29 + tweak_x)
        self.y = int(y * 29 - 12 + tweak_y)

        """ # 画面内での座標
        self.rect.left = self.x - SpritePlayer.scroll_sum
        self.rect.top = self.y
        """

        # スプライトのサイズ
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # 初期位置に描画
        self.rect = Rect(self.x - SpritePlayer.initial_scroll_sum, self.y, self.width, self.height)
        screen.blit(self.image, self.rect)

        # 描画する範囲
        self.START_RANGE = -150
        self.END_RANGE = 480

        # トゲを生やすか
        self.isThorns = False
        self.thorns_img = LoadImage.image_list['block38']
        self.thorns_tweak_x = self.width / 2 - self.thorns_img.get_width() / 2 - 1
        self.thorns_tweak_y = self.height / 2 - self.thorns_img.get_height() / 2 - 1

    def update(self):
        # 画面スクロール
        self.rect.left = self.x - SpritePlayer.scroll_sum

        # 画面内の領域のみ描画
        if self.START_RANGE < self.x - SpritePlayer.scroll_sum < self.END_RANGE:
            # トゲを生やす場合
            if self.isThorns:
                thorns_x = self.rect.left + self.thorns_tweak_x
                thorns_y = self.rect.top + self.thorns_tweak_y
                self.screen.blit(self.thorns_img, (thorns_x, thorns_y))

            if not self.isHide:
                self.screen.blit(self.image, self.rect)


class SpritePlayer(pygame.sprite.Sprite):
    # 初期座標
    initial_x = initial_y = initial_scroll_sum = 0

    scroll = 0  # 1フレームの画面スクロール値
    scroll_sum = 0  # 画面スクロール量の合計

    FALL_ACCELERATION = 0.25  # 落下加速度

    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen
        self.name = 'player'

        # 画像の格納
        img = LoadImage.image_list
        self.image = img['player1']
        self.img_right = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5']]
        self.img_left = [pygame.transform.flip(img, True, False) for img in self.img_right]

        self.x_speed = self.y_speed = 0.0  # 速度
        self.max_speed = 0  # x方向の最大速度 （変数）
        self.JUMP_SPEED = 0  # ジャンプ速度

        self.AIR_MAX_SPEED = 3  # 空中加速時の最大速度

        self.isGrounding = True  # 地面に着地しているか
        self.isJump = False  # ジャンプモーション中か
        self.isDeath = False  # 敵に当たったかどうか

        self.goal = None  # ゴールブロックを格納するオブジェクト
        self.dive_dokan = None  # 潜っている土管を格納するオブジェクト

        # 初期座標セット
        self.x = SpritePlayer.initial_x
        self.y = SpritePlayer.initial_y
        SpritePlayer.scroll_sum = SpritePlayer.initial_scroll_sum
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = Rect(self.x, self.y, self.width, self.height)

    def update(self, image):
        self.rect.left = self.x
        self.rect.top = self.y
        self.screen.blit(image, self.rect)

    # 空中時の最大速度を計算
    def limit_air_speed(self):
        if abs(self.x_speed) < self.AIR_MAX_SPEED:
            self.max_speed = self.AIR_MAX_SPEED
        else:
            self.max_speed = abs(self.x_speed)
