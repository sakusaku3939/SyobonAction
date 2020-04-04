import pygame
from pygame.locals import *
import sys
from time import *

from Image import LoadImage
from Stage import Stage
from Player import Player

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
            clock.tick(FPS)

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
        self.stage = Stage(screen, 1, '1-1')
        self.stage.draw()

        self.init_flag = True
        self.scroll = 0

        remain_show()

        self.player = Player(screen)

        self.main()

    def main(self):
        while 1:
            screen.fill((160, 180, 250))

            self.stage.update(self.player)
            self.player.update(self.stage)

            # スペースキーで3倍速
            variable_FPS = FPS * (3 if pygame.key.get_pressed()[K_SPACE] else 1)
            clock.tick(variable_FPS)

            pygame.display.update(Rect(0, 0, 480, 420))

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
                        self.stage.image_object_list.clear()
                        return


if __name__ == "__main__":
    main()
