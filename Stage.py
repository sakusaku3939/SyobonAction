import pygame
import xlrd
import sys
import tkinter
from tkinter import messagebox

from Image import Sprite


class Stage:
    # 画像オブジェクトを格納するリスト
    image_object_list = []

    def __init__(self, screen, block_color, sheet_name):
        # ステージのブロックの色 （1～4）
        self.screen = screen
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
        sheet_data = [sheet.col_values(row) for row in range(sheet.ncols)]
        self.stage_data = [[int(item) for item in row if item != ''] for row in sheet_data]
        self.draw()

    def draw(self):
        # ステージデータから取得
        for x, list_data in enumerate(self.stage_data):
            for y, data in enumerate(list_data):
                # 一つ前のステージデータを取得
                try:
                    stage_position_top = self.stage_data[x][y - 1]
                    stage_position_down = self.stage_data[x][y + 1]
                    stage_position_left = self.stage_data[x - 1][y]
                    stage_position_right = self.stage_data[x + 1][y]
                except IndexError:
                    pass

                # 壊れるブロック
                self.add('block1', data, x, y, range(1, 17), True)

                # はてなブロック
                self.add('block2', data, x, y, range(17, 29), True)

                # 隠しブロック
                self.add('block3', data, x, y, range(29, 41), True)

                # 硬いブロック
                self.add('block4', data, x, y, range(41, 43), True)

                # 足場ブロック
                if data == 43:
                    if stage_position_top != 43:
                        self.add('block5', data, x, y, None, True)
                    else:
                        self.add('block6', data, x, y, None, True)

                # 落ちる足場ブロック
                if data == 44:
                    if stage_position_top != 44:
                        self.add('block5', data, x, y, None, True)
                    else:
                        self.add('block6', data, x, y, None, True)

                # 針
                self.add('block7', data, x, y, 47, True)

                # ポール
                self.add('block4', data, x, y, range(48, 50))
                self.add('goal_pole', data, x, y, range(50, 52), False, 3, -10)

                # 顔付きの雲
                self.add('cloud2', data, x, y, 75)

                # 土管
                self.add('dokan1', data, x, y, range(81, 85))
                self.add('dokan1', data, x, y, 79)
                self.add('dokan2', data, x, y, 80, False, -1, 1)

                # 草
                self.add('grass', data, x, y, 88)

                # 山
                self.add('mountain', data, x, y, 89)

                # 中間地点
                self.add('halfway', data, x, y, 95)

                # ゴール塔
                self.add('end', data, x, y, 96)

                # まるい敵
                self.add('enemy', data, x, y, range(99, 102))

                # 甲羅亀
                self.add('koura1', data, x, y, range(102, 104), False, 0, -12)

    # 画像データをImageクラスに追加
    def add(self, img_name, data, img_x, img_y, range_function, color=False, tweak_x=0, tweak_y=0):
        # ブロックの色を変更
        name = f'block{int(img_name[-1:]) + self.mode}' if color else img_name

        append = (lambda: self.image_object_list.append(Sprite(self.screen, name, img_x, img_y, tweak_x, tweak_y)))

        # dataと一致しているか確認する場合
        if type(range_function) is int:
            if data == range_function:
                append()

        # 呼び出し元でdataと一致しているか確認する場合
        elif range_function is None:
            append()

        else:  # 画像のパターンマッチング
            for i in range_function:
                if data == i:
                    append()

    def update(self, player):
        for image in self.image_object_list:
            image.update(player.scroll)
