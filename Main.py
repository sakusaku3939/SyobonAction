import pygame
import xlrd
from pygame.locals import *
import sys
import numpy as np
from time import *
import tkinter
from tkinter import messagebox

from Image import LoadImage

pygame.init()

# ウィンドウの設定
screen = pygame.display.set_mode((480, 420))
pygame.display.set_caption("しょぼんのアクション")

# FPS
clock = pygame.time.Clock()
FPS = 60

# ゲームの状態
#   0: タイトル画面
#   1: ステージ1-1
#   2: ステージ1-2
#   3: ステージ1-3
#   4: ステージ1-4
GAME_STATE = 0

# 残機数
REMAIN = 2


def main():
    LoadImage()

    while 1:
        # タイトル画面
        if GAME_STATE == 0:
            Title()
        # ステージ 1-1
        elif GAME_STATE == 1:
            Stage_1()


class Stage:
    def __init__(self, block_color, sheet_name):
        # ステージのブロックの色 （1～4）
        self.mode = 7 * (block_color - 1)

        # Excelからステージデータを取得
        try:
            file = xlrd.open_workbook('res/ステージデータ.xlsx')
            sheet = file.sheet_by_name(sheet_name)
        except FileNotFoundError:
            root = tkinter.Tk()
            root.withdraw()
            messagebox.showerror("エラー", "ステージデータ.xlsxが見つかりませんでした")
            pygame.quit()
            sys.exit()
        except xlrd.biffh.XLRDError:
            root = tkinter.Tk()
            root.withdraw()
            messagebox.showerror("エラー", f"シート'{sheet_name}'が見つかりませんでした")
            pygame.quit()
            sys.exit()

        # ステージデータを読み込む
        sheet_data = [sheet.row_values(row) for row in range(16)]
        self.stage_data = [[int(item) for item in row if item != ''] for row in sheet_data]

    # ステージの描画
    def draw(self, scroll):
        img = LoadImage.image_list

        # 画像の描画
        def iDraw(img_data, img_x, img_y, tweak_x=0, tweak_y=0):
            screen.blit(img_data, (tweak_x + img_x * 29 - scroll, tweak_y + img_y * 29 - 12))

        # ステージデータから取得
        for y, list_data in enumerate(self.stage_data):
            for x, data in enumerate(list_data):
                # 一つ前のステージデータを取得
                try:
                    stage_position_top = self.stage_data[y - 1][x]
                    stage_position_down = self.stage_data[y + 1][x]
                    stage_position_left = self.stage_data[y][x - 1]
                    stage_position_right = self.stage_data[y][x + 1]
                except IndexError:
                    pass

                # ブロック
                for i in range(1, 17):
                    if data == i:
                        iDraw(img[f'block{1 + self.mode}'], x, y)
                        # Block(1+self.mode, x, y)

                # はてなブロック
                for i in range(17, 29):
                    if data == i:
                        iDraw(img[f'block{2 + self.mode}'], x, y)

                # 隠しブロック
                for i in range(29, 41):
                    if data == i:
                        iDraw(img[f'block{3 + self.mode}'], x, y)

                # 硬いブロック
                for i in range(41, 43):
                    if data == i:
                        iDraw(img[f'block{4 + self.mode}'], x, y)

                # 足場ブロック
                if data == 43:
                    if stage_position_top != 43:
                        # iDraw(img[f'block{5 + self.mode}'], x, y)
                        Block(5 + self.mode, x, y)
                    else:
                        iDraw(img[f'block{6 + self.mode}'], x, y)
                if data == 44:
                    if stage_position_top != 44:
                        iDraw(img[f'block{5 + self.mode}'], x, y)
                    else:
                        iDraw(img[f'block{6 + self.mode}'], x, y)

                # 針
                if data == 47:
                    iDraw(img[f'block{7 + self.mode}'], x, y)

                # ポール
                for i in range(48, 50):
                    if data == i:
                        iDraw(img[f'block4'], x, y)

                # 中間地点
                if data == 95:
                    iDraw(img['halfway'], x, y)

                # 土管
                for i in range(81, 85):
                    if data == i or data == 79:
                        iDraw(img['dokan1'], x, y)
                if data == 80:
                    iDraw(img['dokan2'], x, y, -1, 1)

                # 草
                if data == 88:
                    iDraw(img['grass'], x, y)

                # 山
                if data == 89:
                    iDraw(img['mountain'], x, y)

                # 顔付きの雲
                if data == 75:
                    iDraw(img['cloud2'], x, y)

                # まるい敵
                for i in range(99, 102):
                    if data == i:
                        iDraw(img['enemy'], x, y)

                # 甲羅亀
                for i in range(102, 104):
                    if data == i:
                        iDraw(img['koura1'], x, y, 0, -12)


class Block(pygame.sprite.Sprite):
    def __init__(self, block_number, x, y):
        pygame.sprite.Sprite.__init__(self)

        image = LoadImage.image_list[f'block{block_number}']
        pos = (x * 29, y * 29 - 12)

        screen.blit(image, pos)
        self.rect = image.get_rect()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        img = LoadImage.image_list
        self.image = img['player1']
        self.img_right = [img['player1'], img['player2'], img['player3'], img['player4']]
        self.img_left = [pygame.transform.flip(i, True, False) for i in self.img_right]

        width = self.image.get_width()
        height = self.image.get_height()
        self.rect = Rect(60, 329, width, height)

        self.x_speed = self.y_speed = 0  # 速度
        self.ACCELERATION = 0.13  # 加速度
        self.MAX_SPEED = 4  # 最大速度

        self.isGrounding = True  # 落下しているか
        self.FALL_ACCELERATION = 0.3  # 落下加速度

        self.isJump = False  # ジャンプモーション中か
        self.JUMP_SPEED = -7.4  # ジャンプ速度
        self.ADD_JUMP_SPEED = -2.1  # 追加のジャンプ速度
        self.jump_time = 0  # ジャンプ時間

    def update(self):
        pressed_key = pygame.key.get_pressed()

        # 歩行アニメーション
        animation = int(self.rect.left / 20) % 2

        # 地面
        if self.rect.top < 329:
            self.isGrounding = False
            self.y_speed += self.FALL_ACCELERATION
        else:
            self.y_speed = 0
            self.rect.top = 329
            self.isGrounding = True
            self.isJump = False

        # 矢印キー入力
        if pressed_key[K_UP] and self.isGrounding:
            self.isJump = True
            self.y_speed = self.JUMP_SPEED  # ジャンプ

        if pressed_key[K_DOWN]:
            pass

        if pressed_key[K_LEFT]:
            self.x_speed -= self.ACCELERATION if self.x_speed < 0 else 2 * self.ACCELERATION  # 左移動
            self.image = self.img_left[animation]

        elif pressed_key[K_RIGHT]:
            self.x_speed += self.ACCELERATION if self.x_speed > 0 else 2 * self.ACCELERATION  # 右移動
            self.image = self.img_right[animation]

        elif self.isGrounding:
            self.x_speed -= self.ACCELERATION * np.sign(self.x_speed)  # 地面摩擦

        # 最大速度
        self.x_speed = np.clip(self.x_speed, -self.MAX_SPEED, self.MAX_SPEED)

        # 画面外に出ないようにする
        if (self.rect.left + self.x_speed < 0) and not (pressed_key[K_RIGHT] and self.x_speed >= 0):
            self.x_speed = 0
        if (self.rect.left + self.x_speed > 450) and not (pressed_key[K_LEFT] and self.x_speed <= 0):
            self.x_speed = 0

        # ジャンプ
        if not pressed_key[K_UP]:
            self.isJump = False
            self.jump_time = 0
        elif self.isJump:
            # キー長押しでジャンプを長くする
            if self.jump_time >= 8:
                self.isJump = False
                # スピードが最大の時、更にジャンプ速度を追加
                if self.x_speed >= self.MAX_SPEED:
                    self.y_speed += self.ADD_JUMP_SPEED - 0.7
                else:
                    self.y_speed += self.ADD_JUMP_SPEED
            else:
                self.jump_time += 1

        # 描画
        self.rect.left += int(self.x_speed)
        self.rect.top += int(self.y_speed)
        screen.blit(self.image, self.rect)


# 黒画面にして残機を表示
def remain_show():
    screen.fill((0, 0, 0))

    # プレイヤー画像の表示
    img = LoadImage.image_list
    player = img['player1']

    player_rect = player.get_rect()
    player_rect.center = (200, 210)
    screen.blit(player, player_rect)

    # 残機数の表示
    global REMAIN
    font = pygame.font.Font("res/font/msgothic.ttc", 20)
    text = font.render(f"× {REMAIN}", True, (255, 255, 255))
    screen.blit(text, [235, 200])

    REMAIN -= 1

    # 一秒間待機
    pygame.display.update()
    sleep(1)


# タイトル画面
class Title:
    def __init__(self):
        global REMAIN
        REMAIN = 2
        self.goto_stage = 1

        # 画像の読み込み
        img = LoadImage.image_list
        title = img['title']
        player = img['player1']
        block = [img['block5'], img['block6']]
        grass = img['grass']
        mountain = img['mountain']

        screen.fill((160, 180, 250))

        # タイトルロゴの描画
        rect_title = title.get_rect()
        rect_title.center = (240, 85)
        screen.blit(title, rect_title)

        # タイトル文字の描画
        font = pygame.font.Font("res/font/msgothic.ttc", 20)
        text = font.render("Press Enter Key", True, (0, 0, 0))
        screen.blit(text, [160, 250])
        screen.blit(text, [161, 250])

        # 背景の描画
        screen.blit(player, (60, 330))
        screen.blit(grass, (180, 336))
        screen.blit(mountain, (360, 278))

        for i in range(17):
            screen.blit(block[0], (29 * i, 365))
            screen.blit(block[1], (29 * i, 394))

        self.main()

    def main(self):
        while 1:
            pygame.display.update()
            clock.tick(60)

            for event in pygame.event.get():
                # 「×」ボタンが押されたら終了
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == KEYDOWN:
                    # ESCキーが押されたら終了
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                    # ステージ選択
                    if event.key == K_1:
                        self.goto_stage = 1
                    if event.key == K_2:
                        self.goto_stage = 2
                    if event.key == K_3:
                        self.goto_stage = 3
                    if event.key == K_4:
                        self.goto_stage = 4

                    # ENTERキーが押されたらスタート
                    if event.key == 13:
                        global GAME_STATE
                        GAME_STATE = self.goto_stage
                        return


# ステージ1-1
class Stage_1:
    def __init__(self):
        self.stage = Stage(1, '1-1')
        self.init_flag = True
        self.scroll = 0

        remain_show()
        self.player = Player()

        self.main()

    def main(self):
        while 1:
            screen.fill((160, 180, 250))
            self.stage.draw(self.scroll)
            self.player.update()
            pygame.display.update()
            clock.tick(60)

            # # 矢印キー入力
            # pressed_key = pygame.key.get_pressed()
            # if pressed_key[K_UP]:
            #     pass
            # if pressed_key[K_DOWN]:
            #     pass
            # if pressed_key[K_LEFT]:
            #     self.scroll -= 2
            # if pressed_key[K_RIGHT]:
            #     self.scroll += 2

            # スクロールの範囲
            if self.scroll <= 0:
                self.scroll = 0
            elif self.scroll >= 3610:
                self.scroll = 3610

            for event in pygame.event.get():
                # 「×」ボタンが押されたら終了
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == KEYDOWN:
                    # ESCキーが押されたら終了
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    # F1キーが押されたらタイトルに戻る
                    if event.key == K_F1:
                        global GAME_STATE
                        GAME_STATE = 0
                        return


if __name__ == "__main__":
    main()
