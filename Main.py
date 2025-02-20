import tkinter
from tkinter import messagebox

import numpy as np
import pygame
from pygame.locals import *
import sys
from time import *

from Enemy import Enemy
from Image import LoadImage
from Sprite import SpritePlayer
from Sound import Sound
from Stage import Stage
from Player import Player
from Text import Text
from model.PolicyNetwork import PPO, SimpleRewardSystem

pygame.init()

# ウィンドウの設定
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 420
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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

# PPOの設定
state_dim = 2
action_dim = 6
ppo = PPO(state_dim, action_dim, ent_coef=0.1)

is_speed_up = True
prev_player_movement = 0
reward_system = SimpleRewardSystem()

num_episodes = 1000
is_ai_mode = True

def main():
    LoadImage()
    Text()
    Sound()

    while 1:
        # タイトル画面
        if GAME_STATE == 0:
            Title()
        # ステージ 1-1
        elif GAME_STATE == 1:
            for episode in range(num_episodes):
                if GAME_STATE != 1:
                    break
                states, actions, rewards, dones = [], [], [], []
                Stage_1(states, actions, rewards, dones)
                reward_system.update_episode(episode)
                print(f"Episode: {episode}, reward: {rewards[-1]}")

            reward_system.reset()
            state_change(0)
        # ステージ 1-2
        elif GAME_STATE == 2:
            Stage_2()
        # ステージ 1-4
        elif GAME_STATE == 3:
            Stage_3()
        # ステージ 1-4
        elif GAME_STATE == 4:
            Stage_4()


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


# ゲームの状態を変更する
def state_change(state_number):
    global GAME_STATE
    GAME_STATE = state_number
    SpritePlayer.initial_x = 55
    SpritePlayer.initial_y = 320
    SpritePlayer.initial_scroll_sum = 0


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
                        state_change(self.goto_stage)
                        return


# ステージ1-1
class Stage_1:
    def __init__(self, states, actions, rewards, dones):
        self.Stage = Stage(screen, 1, '1-1')
        self.Player = Player(screen, self.Stage, is_ai_mode=is_ai_mode)
        self.Enemy = Enemy(screen)

        self.states = states
        self.actions = actions
        self.rewards = rewards
        self.dones = dones
        self.movements = []

        if not is_ai_mode:
            remain_show()
        Sound.play_BGM('titerman')

        self.main()

    def main(self):
        total_reward = 0
        state = np.array([0, 0])
        global prev_player_movement

        while 1:
            action = ppo.act(state)

            screen.fill((160, 180, 250))

            # 強制アニメーション
            if self.Player.goal_animation():
                global REMAIN
                REMAIN += 1
                state_change(2)
                break
            if self.Player.dokan_animation() or self.Player.death_animation():
                break

            next_state, reward, done, movement = self.Player.update(action, prev_player_movement)

            if next_state is not None:
                self.states.append(state)
                self.actions.append(action)
                self.rewards.append(reward)
                self.dones.append(done)
                self.movements.append(movement)

                state = next_state
                total_reward += reward

            self.Enemy.update()
            self.Player.item_animation()
            self.Stage.update()

            Text.update()

            # スペースキーで2倍速
            global is_speed_up
            if pygame.key.get_pressed()[K_SPACE]:
                is_speed_up = not is_speed_up
            variable_FPS = FPS * (2 if is_speed_up else 1)
            clock.tick(variable_FPS)

            pygame.display.update(Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

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
                        state_change(0)
                        return
                    # oキーが押されたら自殺
                    if event.key == K_o:
                        Stage.player_object.isDeath = True

        prev_player_movement = self.movements[-1]
        ppo.update(self.states, self.actions, self.rewards, self.dones)

# ステージ1-2
class Stage_2:
    def __init__(self):
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showinfo("", "1-2は未実装です")

        # self.Stage = Stage(screen, 1, '1-2')
        # self.Player = Player(screen, self.Stage)
        # self.Enemy = Enemy(screen)

        # remain_show()
        # Sound.play_BGM('titerman')

        self.main()

    def main(self):
        state_change(0)
        return


# ステージ1-3
class Stage_3:
    def __init__(self):
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showinfo("", "1-3は未実装です")

        # self.Stage = Stage(screen, 1, '1-3')
        # self.Player = Player(screen, self.Stage)
        # self.Enemy = Enemy(screen)

        # remain_show()
        # Sound.play_BGM('titerman')

        self.main()

    def main(self):
        state_change(0)
        return


# ステージ1-4
class Stage_4:
    def __init__(self):
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showinfo("", "1-4は未実装です")

        # self.Stage = Stage(screen, 4, '1-4')
        # self.Player = Player(screen, self.Stage)
        # self.Enemy = Enemy(screen)

        # remain_show()
        # Sound.play_BGM('makaimura')

        self.main()

    def main(self):
        state_change(0)
        return


if __name__ == "__main__":
    main()
