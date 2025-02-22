import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import torch.nn.functional as F

from Sprite import SpritePlayer


class PolicyNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(PolicyNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, output_dim),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        return self.fc(x)


class ValueNetwork(nn.Module):
    def __init__(self, input_dim):
        super(ValueNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        return self.fc(x)


class PPO:
    def __init__(self, state_dim, action_dim, lr=1e-4, gamma=0.99, epsilon=0.2, ent_coef=0.1):
        self.policy = PolicyNetwork(state_dim, action_dim)
        self.value = ValueNetwork(state_dim)
        self.optimizer = optim.Adam(
            list(self.policy.parameters()) + list(self.value.parameters()),
            lr=lr
        )
        self.gamma = gamma
        self.clip_epsilon = epsilon
        self.ent_coef = ent_coef
        self.lambda_ = 0.95

        self.buffer_size = 2048
        self.batch_size = 64

        # バッファの初期化
        self.states_buffer = []
        self.actions_buffer = []
        self.rewards_buffer = []
        self.dones_buffer = []
        self.values_buffer = []
        self.returns_buffer = []
        self.advantages_buffer = []
        self.log_probs_buffer = []
        self.next_state = None

        # 損失値の記録用
        self.policy_losses = []
        self.value_losses = []
        self.entropy_losses = []
        self.total_losses = []

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy.to(self.device)
        self.value.to(self.device)

    def act(self, state, env):
        with torch.no_grad():
            state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action_probs = self.policy(state)
            
            # 行動確率の温度パラメータ（高いほどランダム性が増す）
            temperature = 0.2
            action_probs = F.softmax(action_probs / temperature, dim=-1)

            # より探索的な行動選択
            dist = Categorical(action_probs)
            action = dist.sample()  # ランダムサンプリング
            log_prob = dist.log_prob(action)
            value = self.value(state)
            
            # エピソード情報の保存
            self.states_buffer.append(state.squeeze(0).cpu().numpy())
            self.actions_buffer.append(action.item())
            self.log_probs_buffer.append(log_prob.item())
            self.values_buffer.append(value.item())
        
        # 環境で行動を実行し、次の状態を取得
        next_state = env(action.item())
        self.next_state = next_state  # 次の状態を保存
        
        return action.item()

    def compute_gae(self, rewards, values, dones):
        advantages = []
        gae = 0

        # 最後の状態の価値を使用
        next_value = values[-1]  # 最後の状態の価値

        # len(rewards) - 1 から 0 まで逆順に処理
        for step in reversed(range(len(rewards))):
            if step == len(rewards) - 1:
                next_val = next_value
            else:
                next_val = values[step + 1]

            delta = rewards[step] + self.gamma * next_val * (1 - dones[step]) - values[step]
            gae = delta + self.gamma * self.lambda_ * (1 - dones[step]) * gae
            advantages.insert(0, gae)

        return advantages

    def update(self):
        print(f"Current buffer size: {len(self.states_buffer)}/{self.buffer_size}")
        if len(self.states_buffer) < self.buffer_size:
            return None, None, None, None

        # バッファをテンソルに変換
        states = torch.FloatTensor(np.vstack(self.states_buffer)).to(self.device)
        actions = torch.LongTensor(self.actions_buffer).to(self.device)
        old_log_probs = torch.FloatTensor(self.log_probs_buffer).to(self.device)
        rewards = torch.FloatTensor(self.rewards_buffer).to(self.device)
        dones = torch.FloatTensor(self.dones_buffer).to(self.device)
        values = torch.FloatTensor(self.values_buffer).to(self.device)

        # 最後の状態の価値を計算
        with torch.no_grad():
            last_state = states[-1].unsqueeze(0)  # 最後の状態を使用
            next_value = self.value(last_state).cpu().item()

        # GAEの計算
        advantages = self.compute_gae(rewards.cpu().numpy(), 
                                    values.cpu().numpy(), 
                                    dones.cpu().numpy())
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = advantages + values

        loss = None

        # ミニバッチ学習
        for _ in range(10):  # エポック数
            for start_idx in range(0, len(states), self.batch_size):
                # バッチデータの取得
                batch_indices = slice(start_idx, start_idx + self.batch_size)
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]

                # 現在の方策での行動確率
                action_probs = self.policy(batch_states)
                dist = Categorical(action_probs)
                new_log_probs = dist.log_prob(batch_actions)

                # 方策比率
                ratio = torch.exp(new_log_probs - batch_old_log_probs)

                # PPOの目的関数
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # 価値関数の損失
                value_pred = self.value(batch_states).squeeze()
                value_loss = 0.5 * (batch_returns - value_pred).pow(2).mean()

                # エントロピーボーナス
                entropy = dist.entropy().mean()

                # 総損失
                loss = policy_loss + 0.5 * value_loss - self.ent_coef * entropy

                # 最適化
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                torch.nn.utils.clip_grad_norm_(self.value.parameters(), 0.5)
                self.optimizer.step()

        # 損失値を記録
        policy_loss_val = policy_loss.item()
        value_loss_val = value_loss.item()
        entropy_loss_val = entropy.item()
        total_loss_val = loss.item()

        self.policy_losses.append(policy_loss_val)
        self.value_losses.append(value_loss_val)
        self.entropy_losses.append(entropy_loss_val)
        self.total_losses.append(total_loss_val)

        # バッファのクリア
        self.clear_buffers()

        return policy_loss_val, value_loss_val, entropy_loss_val, total_loss_val

    def clear_buffers(self):
        self.states_buffer = []
        self.actions_buffer = []
        self.rewards_buffer = []
        self.dones_buffer = []
        self.values_buffer = []
        self.log_probs_buffer = []

    def get_state(self, player):
        # 基本的な状態
        base_state = np.array([
            player.x + SpritePlayer.scroll_sum,  # x座標
            player.y,                            # y座標
            player.x_speed,                      # x方向速度
            player.y_speed,                      # y方向速度
            float(player.isGrounding),           # 地面接地状態
            float(player.isJump),                # ジャンプ状態
            float(player.isDeath),               # 死亡状態
        ])

        # 周辺の環境情報（例：前方の地形、敵の位置など）も追加可能

        return base_state

    def get_latest_losses(self):
        if not self.total_losses:
            return None, None, None, None
        return (self.policy_losses[-1], self.value_losses[-1],
                self.entropy_losses[-1], self.total_losses[-1])


class SimpleRewardSystem:
    def __init__(self):
        self.goal_x = 3477 + 210
        self.prev_x = 0
        self.current_x = 0
        self.delta_x = 0
        self.best_x = 0
        self.stagnation_count = 0
        self.episode_count = 0
        self.max_stagnation = 50
        self.goal_bonus = 200

    def calculate_reward(self, player_obj):
        current_x = player_obj.x + SpritePlayer.scroll_sum
        self.current_x = current_x

        # 進捗報酬
        progress_ratio = current_x / self.goal_x
        progress_reward = 50 * progress_ratio ** 2

        # 停滞ペナルティ
        stagnation_factor = min(self.stagnation_count, self.max_stagnation)
        time_penalty = -0.3 * stagnation_factor

        # ゴール報酬
        if current_x >= self.goal_x:
            goal_bonus = self.goal_bonus
        elif current_x > self.goal_x * 0.9:
            goal_bonus = self.goal_bonus * 0.7
        else:
            goal_bonus = 0

        # print(f"Reward: velocity={velocity_reward:.2f}, progress={progress_reward:.2f}, "
        #       f"time_penalty={time_penalty:.2f}, goal_bonus={goal_bonus:.2f}")

        total_reward = (
            progress_reward +
            time_penalty +
            goal_bonus
        )

        # 報酬のクリッピング
        total_reward = np.clip(total_reward, -20, 100)

        return total_reward, (current_x >= self.goal_x or player_obj.isDeath)

    def update_episode(self, episode_count):
        self.delta_x = self.current_x - self.prev_x

        if abs(self.delta_x) < 10:
            self.stagnation_count += 1
        else:
            self.stagnation_count = 0

        self.prev_x = self.current_x
        self.episode_count = episode_count

    def reset(self):
        self.prev_x = 0
        self.current_x = 0
        self.delta_x = 0
        self.stagnation_count = 0
        self.episode_count = 0
