import pygame
import xlrd
from pygame.locals import *
import sys
from time import *
import pathlib
import os
import tkinter
from tkinter import messagebox

pygame.init()

screen = pygame.display.set_mode((480, 420))
pygame.display.set_caption("しょぼんのアクション")

# ゲームの状態
#   0: タイトル画面
#   1: ステージ1-1
#   2: ステージ1-2
#   3: ステージ1-3
#   4: ステージ1-4
game_state = 0

# 残機数
remain = 2


def main():
    while 1:
        # タイトル画面
        if game_state == 0:
            Title()
        # ステージ 1-1
        elif game_state == 1:
            Stage_1()


# 画像データの読み込み
def load_image():
    image_list = {'title': pygame.image.load("res/title.png").convert()}
    folder_list = ['player', 'enemy', 'bg', 'item', 'block']

    # 画像データを読み込む
    for folder in folder_list:
        file_list = pathlib.Path(f'res/{folder}/').glob('*.png')

        for file in file_list:
            image_name = os.path.splitext(file.name)[0]
            image = pygame.image.load(f"res/{folder}/{file.name}").convert()
            image_list[image_name] = image

    # 画像の透過
    for image in image_list.values():
        image.set_colorkey((153, 255, 255), RLEACCEL)

    return image_list


# ステージデータの読み込み
def stage_load(sheet_name):
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
    stage_data = [[int(item) for item in row if item != ''] for row in sheet_data]

    return stage_data


# ステージの描画
def stage_draw(block_mode, stage_data, scroll):
    # ステージのブロックの色
    mode = 7 * (block_mode - 1)

    # 画像の読み込み
    img = load_image()

    stage_position = {}

    # 画像の描画
    def draw(img_data, img_x, img_y, tweak_x=0, tweak_y=0):
        screen.blit(img_data, (tweak_x + img_x * 29 - scroll, tweak_y + img_y * 29 - 12))

    test = 0

    # ステージデータから取得
    for y, list_data in enumerate(stage_data):
        for x, data in enumerate(list_data):
            stage_position[(x, y)] = data

            # ブロック
            for i in range(1, 17):
                if data == i:
                    draw(img[f'block{1 + mode}'], x, y)

            # はてなブロック
            for i in range(17, 29):
                if data == i:
                    draw(img[f'block{2 + mode}'], x, y)

            # 隠しブロック
            for i in range(29, 41):
                if data == i:
                    draw(img[f'block{3 + mode}'], x, y)

            # 硬いブロック
            for i in range(41, 43):
                if data == i:
                    draw(img[f'block{4 + mode}'], x, y)

            # 足場ブロック
            if data == 43:
                # @TODO 周りのブロックを調べる処理の追加
                if x < test:
                    if stage_position[(x, y - 1)] != 43:
                        draw(img[f'block{5 + mode}'], x, y)
                    else:
                        draw(img[f'block{6 + mode}'], x, y)
            # if data == 44:
            #     draw(img[f'block{6 + mode}'], x, y)

            # 針
            if data == 47:
                draw(img[f'block{7 + mode}'], x, y)

            # 硬いブロック
            for i in range(48, 43):
                if data == i:
                    draw(img[f'block{4 + mode}'], x, y)
            # # 中間地点
            # if data == 30:
            #     draw(img['halfway'], x, y)
            #
            # # 土管
            # if data == 40:
            #     draw(img['dokan1'], x, y)
            # if data == 41:
            #     draw(img['dokan2'], x, y, -1, 1)
            #
            # # 山
            # if data == 80:
            #     draw(img['mountain'], x, y)
            #
            # # 草
            # if data == 81:
            #     draw(img['grass'], x, y)
            #
            # # 顔付きの雲
            # if data == 82:
            #     draw(img['cloud2'], x, y)
            #
            # # まるい敵
            # if data == 50:
            #     draw_enemy(img['enemy'], x, y)
            #
            # # 甲羅亀
            # if data == 51:
            #     draw_enemy(img['koura1'], x, y, 0, -12)
            test = x


# 黒画面にして残機を表示
def remain_show():
    screen.fill((0, 0, 0))

    # プレイヤー画像の表示
    img = load_image()
    player = img['player1']

    player_rect = player.get_rect()
    player_rect.center = (200, 210)
    screen.blit(player, player_rect)

    # 残機数の表示
    global remain
    font = pygame.font.Font("res/font/msgothic.ttc", 20)
    text = font.render(f"× {remain}", True, (255, 255, 255))
    screen.blit(text, [235, 200])

    remain -= 1

    # 一秒間待機
    pygame.display.update()
    sleep(1)


# タイトル画面
class Title:
    def __init__(self):
        global remain
        remain = 2
        self.goto_stage = 1

        # 画像の読み込み
        img = load_image()
        title = img['title']
        player = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5'], img['player6']]
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
        screen.blit(player[0], (60, 330))
        screen.blit(grass, (180, 336))
        screen.blit(mountain, (360, 278))

        for i in range(17):
            screen.blit(block[0], (29 * i, 365))
            screen.blit(block[1], (29 * i, 394))

        self.main()

    def main(self):
        while 1:
            pygame.display.update()

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
                        global game_state
                        game_state = self.goto_stage
                        return


# ステージ1-1
class Stage_1:
    def __init__(self):
        # 画像の読み込み
        img = load_image()
        self.player = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5'], img['player6']]

        self.stage_data = stage_load('1-1')
        self.init_flag = True
        self.scroll = 0

        remain_show()
        screen.fill((160, 180, 250))
        stage_draw(1, self.stage_data, self.scroll)
        self.main()

    def main(self):
        while 1:
            pygame.display.update()

            # 矢印キー入力
            pressed_key = pygame.key.get_pressed()
            if pressed_key[K_UP]:
                pass
            if pressed_key[K_DOWN]:
                pass
            if pressed_key[K_LEFT]:
                self.scroll -= 2
            if pressed_key[K_RIGHT]:
                self.scroll += 2

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
                        global game_state
                        game_state = 0
                        return


if __name__ == "__main__":
    main()
