import pygame
import xlrd
import sys
import tkinter
from tkinter import messagebox

from Image import Sprite, SpriteEnemy, SpritePlayer


class Stage:
    # プレイヤーオブジェクトを格納するリスト
    player_object = None
    # ブロックオブジェクトを格納するリスト
    block_object_list = []
    # 敵オブジェクトを格納するリスト
    enemy_object_list = []

    def __init__(self, screen, block_color, sheet_name):
        self.screen = screen
        Stage.player_object = SpritePlayer(screen)

        # オブジェクトリストの初期化
        self.block_object_list.clear()
        self.enemy_object_list.clear()

        # ステージのブロックの色 （1～4）
        self._mode = 7 * (block_color - 1)

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

        # 当たり判定を行わない背景画像
        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']

    def bg_update(self):
        for image in self.block_object_list:
            if image.name in self.bg:
                image.update()

    def update(self):
        for image in self.block_object_list:
            if image.name not in self.bg:
                image.update()

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
                self.block_add('block1', data, x, y, range(1, 17), color=True)

                # はてなブロック
                self.block_add('block2', data, x, y, range(17, 29), color=True)

                # 隠しブロック
                self.block_add('block3', data, x, y, range(29, 41), color=True)

                # 硬いブロック
                self.block_add('block4', data, x, y, range(41, 43), color=True)

                # 足場ブロック
                if data == 43:
                    if stage_position_top != 43:
                        self.block_add('block5', data, x, y, color=True)
                    else:
                        self.block_add('block6', data, x, y, color=True)

                # 落ちる足場ブロック
                if data == 44:
                    if stage_position_top != 44:
                        self.block_add('block5', data, x, y, color=True)
                    else:
                        self.block_add('block6', data, x, y, color=True)

                # 針
                self.block_add('block7', data, x, y, 47, color=True)

                # ポール
                self.block_add('block4', data, x, y, range(48, 50))
                self.block_add('goal_pole', data, x, y, range(50, 52), tweak_x=3, tweak_y=-10)

                # 顔付きの雲
                self.block_add('cloud2', data, x, y, 75)

                # 土管
                self.block_add('dokan1', data, x, y, range(81, 85))
                self.block_add('dokan1', data, x, y, 79)
                self.block_add('dokan2', data, x, y, 80, tweak_x=-1, tweak_y=1)

                # 草
                self.block_add('grass', data, x, y, 88)

                # 山
                self.block_add('mountain', data, x, y, 89)

                # 中間地点
                self.block_add('halfway', data, x, y, 95)

                # ゴール塔
                self.block_add('end', data, x, y, 96)

                # まるい敵
                self.enemy_add('enemy', data, x, y, range(99, 102))

                # 甲羅亀
                self.enemy_add('koura1', data, x, y, range(102, 104), tweak_x=0, tweak_y=-12)

    # ブロックデータをSpriteクラスに追加
    def block_add(self, img_name, data, img_x, img_y, range_function=None, color=False, tweak_x=0, tweak_y=0):
        # ブロックの色を変更
        name = f'block{int(img_name[-1:]) + self._mode}' if color else img_name

        # block_object_listに追加
        append = (lambda: self.block_object_list.append(
            Sprite(self.screen, name, img_x, img_y, tweak_x, tweak_y)
        ))
        self._add(data, range_function, append)

    # 敵データをSpriteクラスに追加
    def enemy_add(self, name, data, img_x, img_y, range_function=None, tweak_x=0, tweak_y=0):
        # enemy_object_listに追加
        append = (lambda: self.enemy_object_list.append(
            SpriteEnemy(self.screen, name, img_x, img_y, tweak_x, tweak_y)
        ))
        self._add(data, range_function, append)

    # 画像のパターンマッチング
    def _add(self, data, range_function, append):
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