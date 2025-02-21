import tkinter
from tkinter import messagebox

import numpy as np
import pygame
from pygame.locals import *
import sys
from time import *
import matplotlib.pyplot as plt

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
state_dim = 6  # x, y, x_speed, y_speed, isGrounding, isJump
action_dim = 6
ppo = PPO(state_dim, action_dim, ent_coef=0.1)

is_speed_up = True
prev_player_movement = 0
reward_system = SimpleRewardSystem()

num_episodes = 2000
is_ai_mode = True

def main():
    LoadImage()
    Text()
    Sound()

    # 学習結果の記録用
    all_rewards = []
    all_distances = []
    all_policy_losses = []
    all_value_losses = []
    all_entropy_losses = []
    all_total_losses = []
    WINDOW_SIZE = 2

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
                
                # 損失値を取得
                policy_loss, value_loss, entropy_loss, total_loss = ppo.get_latest_losses()
                if total_loss is not None:
                    all_policy_losses.append(policy_loss)
                    all_value_losses.append(value_loss)
                    all_entropy_losses.append(entropy_loss)
                    all_total_losses.append(total_loss)
                
                # 報酬と距離を記録
                all_rewards.append(rewards[-1])
                current_x = states[-1][0] if states else 0
                all_distances.append(current_x)
                
                # エピソード情報の出力
                loss_str = f", loss: {total_loss:.4f}" if total_loss is not None else ""
                print(f"Episode: {episode}, reward: {rewards[-1]}, distance: {current_x:.1f}{loss_str}")

            # 全エピソード終了後にプロット
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), height_ratios=[2, 1])
            
            # 報酬と距離のプロット（上段）
            episodes = range(len(all_rewards))
            ax1.plot(episodes, all_rewards, 'r-', label='Reward (per episode)')
            ax1.tick_params(axis='y', labelcolor='r')
            
            # 報酬の軸範囲を設定
            min_reward = min(all_rewards)
            max_reward = max(all_rewards)
            margin = (max_reward - min_reward) * 0.1
            ax1.set_ylim([min_reward - margin, max_reward + margin])

            # 距離の移動平均プロット
            if len(all_distances) >= WINDOW_SIZE:
                moving_avg_distances = []
                for i in range(0, len(all_distances) - WINDOW_SIZE + 1, WINDOW_SIZE):
                    window = all_distances[i:i + WINDOW_SIZE]
                    avg = sum(window) / WINDOW_SIZE
                    moving_avg_distances.append(avg)
                
                plot_indices = range(0, len(all_distances) - WINDOW_SIZE + 1, WINDOW_SIZE)
                ax1_twin = ax1.twinx()
                ax1_twin.plot(plot_indices, moving_avg_distances, 'b-',
                        label=f'Distance ({WINDOW_SIZE}-episode average)')
                ax1_twin.tick_params(axis='y', labelcolor='b')
                
                # 距離の軸範囲を設定
                min_dist = -1.0
                max_dist = max(moving_avg_distances)
                margin = max_dist * 0.1
                ax1_twin.set_ylim([min_dist, max_dist + margin])

            # 損失値のプロット（下段）
            episodes = range(len(all_total_losses))
            ax2.plot(episodes, all_policy_losses, 'r-', label='Policy Loss', alpha=0.5)
            ax2.plot(episodes, all_value_losses, 'b-', label='Value Loss', alpha=0.5)
            ax2.plot(episodes, all_entropy_losses, 'g-', label='Entropy Loss', alpha=0.5)
            ax2.plot(episodes, all_total_losses, 'k-', label='Total Loss')
            ax2.set_xlabel('Episode')
            ax2.set_ylabel('Loss')
            ax2.grid(True, alpha=0.3)
            ax2.legend(loc='upper left')

            # 凡例の設定（上段）
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax1_twin.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            plt.suptitle('Learning Progress')
            plt.tight_layout()
            plt.show()

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
        
        # 報酬システムの初期化を追加
        self.reward_system = SimpleRewardSystem()

        if not is_ai_mode:
            remain_show()
        Sound.play_BGM('titerman')

        self.main()

    def get_state(self, player):
        return np.array([
            player.x + SpritePlayer.scroll_sum,  # x座標
            player.y,                            # y座標
            player.x_speed,                      # x方向速度
            player.y_speed,                      # y方向速度
            float(player.isGrounding),           # 地面接地状態
            float(player.isJump)                 # ジャンプ状態
        ])

    def main(self):
        state = self.get_state(self.Player.player)
        total_reward = 0

        while 1:

            screen.fill((160, 180, 250))

            # 強制アニメーション
            if self.Player.goal_animation():
                global REMAIN
                REMAIN += 1
                state_change(2)
                break
            if self.Player.dokan_animation() or self.Player.death_animation():
                break

            # プレイヤーの更新処理を追加
            action = ppo.act(state, self.Player.update)

            next_state = self.get_state(self.Player.player)
            reward, done = self.reward_system.calculate_reward(self.Player.player)

            if next_state is not None:
                self.states.append(state)
                self.actions.append(action)
                self.rewards.append(reward)
                self.dones.append(done)
                self.movements.append(self.Player.player.x - state[0])

                # バッファに追加
                ppo.rewards_buffer.append(reward)
                ppo.dones_buffer.append(done)
                
                # 定期的に更新
                if len(ppo.states_buffer) >= ppo.buffer_size:
                    ppo.update()

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

        ppo.update()

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
