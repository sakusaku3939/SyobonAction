import pygame
import xlrd
import sys
import tkinter
from tkinter import messagebox

from Sprite import SpriteBlock, SpriteObject, SpritePlayer


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
        Stage.block_object_list.clear()
        Stage.enemy_object_list.clear()

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
        self.stage_data = [[item for item in row if item != ''] for row in sheet_data]
        self.draw()

        # 当たり判定を行わない背景画像
        self.bg = ['mountain', 'grass', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'end', 'halfway', 'round',
                   'triangle', 'goal_pole']

    def update(self):
        for image in self.block_object_list:
            # 背景画像を以外を描画
            if image.name not in self.bg:
                image.update()

            # 画面外になったらオブジェクト削除
            if image.rect.left < image.START_RANGE:
                image.remove()
                self.block_object_list.remove(image)

    def draw(self):
        # ステージデータから取得
        for x, list_data in enumerate(self.stage_data):
            for y, data in enumerate(list_data):
                # 一つ前のステージデータを取得
                try:
                    stage_position_up = self.stage_data[x][y - 1]
                    stage_position_down = self.stage_data[x][y + 1]
                    stage_position_left = self.stage_data[x - 1][y]
                    stage_position_right = self.stage_data[x + 1][y]
                except IndexError:
                    stage_position_up = 0
                    stage_position_down = 0
                    stage_position_left = 0
                    stage_position_right = 0

                # 壊れるブロック
                self.block_add('block1', data, x, y, start=1, end=1.2, color=True)
                self.block_add('block1', data, x, y, start=1.4, end=2.6, color=True)

                # 近づくと落ちるブロック
                if data == 1.3:
                    group = 'end' if stage_position_right != 1.3 else ''
                    self.block_add('block1', data, x, y, group=group, color=True)

                # はてなブロック
                self.block_add('block2', data, x, y, start=3, end=4.1, color=True)

                # 隠しブロック
                self.block_add('block3', data, x, y, start=5, end=6.1, color=True)

                # 硬いブロック
                self.block_add('block4', data, x, y, start=7, end=7.1, color=True)

                # 足場ブロック
                if data == 8:
                    if stage_position_up != 8:
                        self.block_add('block5', data, x, y, color=True)
                    else:
                        self.block_add('block6', data, x, y, color=True)

                # 落ちる足場ブロック
                if data == 8.1:
                    if stage_position_up != 8.1:
                        group = 'start' if stage_position_left != 8.1 else ''
                        self.block_add('block5', data, x, y, group=group, color=True)
                    else:
                        group = 'end' if stage_position_right != 8.1 else ''
                        self.block_add('block6', data, x, y, group=group, color=True)

                # 針
                self.block_add('block7', data, x, y, 40, color=True)

                # ポール
                self.block_add('goal_pole', data, x, y, 9.1, tweak_x=3, tweak_y=-10)

                # 光線
                self.block_add('beam', data, x, y, 9.3, tweak_x=-88, tweak_y=4)

                # 顔付きの雲
                self.block_add('cloud2', data, x, y, start=19.1, end=19.2)

                # 透明のうめぇ
                self.block_add('cloud4', data, x, y, 19.3)

                # 土管
                self.block_add('dokan1', data, x, y, 20)
                self.block_add('dokan1', data, x, y, start=20.2, end=20.5)

                if data == 20.1:
                    if stage_position_up == 20.2:
                        # グループ化
                        self.stage_data[x][y] = 20.2
                        self.block_add('dokan2', 20.2, x, y, tweak_x=0, tweak_y=1)
                    else:
                        self.block_add('dokan2', 20.1, x, y, tweak_x=0, tweak_y=1)

                # 草
                self.block_add('grass', data, x, y, 22)

                # 山
                self.block_add('mountain', data, x, y, 22.1)

                # 中間地点
                self.block_add('halfway', data, x, y, 24)

                # ゴール塔
                self.block_add('end', data, x, y, 24.1)

                # まるい敵
                self.enemy_add('enemy', data, x, y, start=27, end=27.2)

                # 甲羅亀
                self.enemy_add('koura1', data, x, y, start=28, end=28.1, tweak_x=0, tweak_y=-12)

                # 飛ぶ魚
                self.enemy_add('fish1', data, x, y, 29, tweak_x=10)
                self.enemy_add('fish2', data, x, y, start=29.1, end=29.2, tweak_x=-10)

    def block_add(self, img_name, data, img_x, img_y, match=0.0,
                  start=0.0, end=0.0, tweak_x=0, tweak_y=0, group='', color=False):
        # ブロックの色を変更
        name = f'block{int(img_name[-1:]) + self._mode}' if color else img_name

        # block_object_listに追加
        append = (lambda: self.block_object_list.append(
            SpriteBlock(self.screen, name, data, img_x, img_y, tweak_x, tweak_y, group)
        ))

        self._add(append, data, match, start, end)

    def enemy_add(self, name, data, img_x, img_y, match=0.0, start=0.0, end=0.0, tweak_x=0, tweak_y=0):
        # enemy_object_listに追加
        append = (lambda: self.enemy_object_list.append(
            SpriteObject(self.screen, name, data, img_x, img_y, tweak_x, tweak_y)
        ))

        self._add(append, data,  match, start, end)

    def _add(self, append, data, match, start, end):
        # dataと一致しているか確認する場合
        if match != 0.0:
            if data == match:
                append()

        # 画像のパターンマッチング
        elif start != 0.0 or end != 0.0:
            start = int(start * 10)
            end = int(end * 10)
            for i in range(start, end + 1):
                if data == i / 10:
                    append()

        else:  # 呼び出し元でdataと一致しているか確認する場合
            append()
