import pygame
from pygame.locals import *
import sys
from time import *
import pathlib
import os


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


def main():
    img = load_image()

    title = Title(img)
    stage_1 = Stage_1(img)

    # # 画像のセット
    # player = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5'], img['player6']]
    # enemy = img['enemy']
    # big_enemy = img['big_enemy']
    # tuno = img['tuno']
    # missile = img['missile']
    # koura = [img['koura1'], img['koura2']]
    # robot = [img['robot1'], img['robot2']]
    # boon = [img['boon1'], img['boon2']]
    # dokan = img['dokan']
    # bear = img['bear']
    # dosun = [img['dosun1'], img['dosun2']]
    # boss = [img['boss1'], img['boss2'], img['boss3'], img['boss4']]
    # chicken = img['chicken']
    # dokan_fire = img['dokan_fire']
    # magma_fire = img['magma_fire']
    # boss_fire = img['boss_fire']

    while 1:
        # タイトル画面
        if game_state == 0:
            title.main()
        # ステージ 1-1
        elif game_state == 1:
            stage_1.main()

        pygame.display.update()


# 画像データの読み込み
def load_image():
    # 画像データを格納
    image_list = {'title': pygame.image.load("res/title.png").convert()}
    folder_list = ['player', 'enemy', 'bg', 'item', 'block']

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


# タイトル画面
class Title:
    def __init__(self, img):
        self.stage_place = 1

        # 画像の読み込み
        self.title = img['title']
        self.player = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5'], img['player6']]

        # タイトルの座標をセット
        self.rect_title = self.title.get_rect()
        self.rect_title.center = (240, 85)

        # 描画
        screen.fill((160, 180, 250))
        screen.blit(self.title, self.rect_title)
        screen.blit(self.player[0], (0, 13))

        # @TODO タイトル画面の作成 ・ 配置

    def main(self):
        global game_state

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
                    self.stage_place = 1
                if event.key == K_2:
                    self.stage_place = 2
                if event.key == K_3:
                    self.stage_place = 3
                if event.key == K_4:
                    self.stage_place = 4

                # ENTERキーが押されたらスタート
                if event.key == 13:
                    game_state = self.stage_place


# ステージ1-1
class Stage_1:
    def __init__(self, img):
        # 画像の読み込み
        player = [img['player1'], img['player2'], img['player3'], img['player4'], img['player5'], img['player6']]
        enemy = img['enemy']
        dokan = img['dokan']
        koura = [img['koura1'], img['koura2']]

    def main(self):
        screen.fill((160, 180, 250))

        # @TODO ステージデータの読み取り機能追加

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


if __name__ == "__main__":
    main()
