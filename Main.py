import pygame
from pygame.locals import *
import sys
from time import *

from Enemy import Enemy
from Image import LoadImage, Sprite
from Sound import Sound
from Stage import Stage
from Player import Player

pygame.init()

# ウィンドウの設定
screen = pygame.display.set_mode((480, 420))
pygame.display.set_caption("しょぼんのアクション")
pygame.display.set_icon(pygame.image.load(f"res/icon.ico"))

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
    Sound()

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

    global REMAIN
    sign = ""
    tweak = 0

    # 符号調整
    if REMAIN < 0:
        sign = "-"

    # 残機数の表示
    font = pygame.font.SysFont("msgothicmsuigothicmspgothic", 20)
    for count, t in enumerate(f"× {sign}{abs(REMAIN)}"):
        text_x = 235 + count * 11
        text = font.render(t, True, (255, 255, 255))
        if count == 1:
            tweak += 10
        elif count == 3:
            tweak += 1
        screen.blit(text, [text_x + tweak, 200])
        screen.blit(text, [text_x + tweak + 1, 200])

    REMAIN -= 1

    # 一秒間待機
    pygame.display.update()
    for i in range(100):
        # スペースキーで2倍速
        if pygame.key.get_pressed()[K_SPACE]:
            sleep(0.005)
        else:
            sleep(0.01)


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
        rect_title.center = (239, 88)
        screen.blit(title, rect_title)

        # タイトル文字の描画
        font = pygame.font.SysFont("msgothicmsuigothicmspgothic", 20)
        for count, t in enumerate("Prece Enter Key"):
            text_x = 160 + count * 11
            text = font.render(t, True, (0, 0, 0))
            screen.blit(text, [text_x, 249])
            screen.blit(text, [text_x + 1, 249])

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

                    # ENTERキー or Zキーが押されたらスタート
                    if event.key == 13 or event.key == 122:
                        global GAME_STATE
                        GAME_STATE = self.goto_stage
                        return


# ステージ1-1
class Stage_1:
    def __init__(self):
        self.stage = Stage(screen, 1, '1-1')
        self.player = Player(screen)
        self.enemy = Enemy(screen)

        remain_show()
        Sound.play_BGM('titerman')

        self.main()

    def main(self):
        while 1:
            screen.fill((160, 180, 250))
            self.stage.bg_update()

            # 死亡時にコンテニュー
            if self.player.death():
                break

            self.stage.update()
            self.player.update()
            self.enemy.update()

            # スペースキーで2倍速
            variable_FPS = FPS * (2 if pygame.key.get_pressed()[K_SPACE] else 1)
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
                        self.stage.block_object_list.clear()
                        return


if __name__ == "__main__":
    main()
