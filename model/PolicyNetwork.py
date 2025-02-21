import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from torch.utils.data import DataLoader, TensorDataset

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
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, epsilon=0.2, ent_coef=0.01):
        self.policy = PolicyNetwork(state_dim, action_dim)
        self.value = ValueNetwork(state_dim)
        self.optimizer = optim.Adam(list(self.policy.parameters()) + list(self.value.parameters()), lr=lr)
        
        self.gamma = gamma
        self.epsilon = epsilon
        self.ent_coef = ent_coef
        
        # バッファサイズとバッチサイズの設定
        self.buffer_size = 2048
        self.batch_size = 64
        
        # バッファの初期化
        self.states_buffer = []
        self.actions_buffer = []
        self.rewards_buffer = []
        self.dones_buffer = []
        self.values_buffer = []
        self.log_probs_buffer = []
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy.to(self.device)
        self.value.to(self.device)

    def act(self, state):
        with torch.no_grad():
            state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action_probs = self.policy(state)
            value = self.value(state)
            
            dist = Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            self.states_buffer.append(state.squeeze(0).cpu().numpy())
            self.actions_buffer.append(action.item())
            self.log_probs_buffer.append(log_prob.item())
            self.values_buffer.append(value.item())
            
        return action.item()

    def compute_gae(self, rewards, values, dones, next_value):
        advantages = []
        gae = 0
        for r, v, done in zip(reversed(rewards), reversed(values), reversed(dones)):
            delta = r + self.gamma * next_value * (1 - done) - v
            gae = delta + self.gamma * 0.95 * (1 - done) * gae
            advantages.insert(0, gae)
            next_value = v
        return advantages

    def update(self):
        if len(self.states_buffer) < self.buffer_size:
            return

        # バッファからデータを取得
        states = torch.FloatTensor(self.states_buffer).to(self.device)
        actions = torch.LongTensor(self.actions_buffer).to(self.device)
        old_log_probs = torch.FloatTensor(self.log_probs_buffer).to(self.device)
        
        # 価値の計算
        with torch.no_grad():
            next_value = self.value(states[-1:]).item()
        
        # GAEの計算
        advantages = self.compute_gae(self.rewards_buffer, self.values_buffer, 
                                    self.dones_buffer, next_value)
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = advantages + torch.FloatTensor(self.values_buffer).to(self.device)
        
        # 正規化
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

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
                surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * batch_advantages
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

        # バッファのクリア
        self.clear_buffers()

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


class SimpleRewardSystem:
    def __init__(self):
        self.goal_x = 3477 + 210
        self.prev_x = 0
        self.current_x = 0
        self.delta_x = 0
        self.stagnation_count = 0
        self.episode_count = 0
        self.max_stagnation = 50
        self.goal_bonus = 200
        
    def calculate_reward(self, player_obj):
        current_x = player_obj.x + SpritePlayer.scroll_sum

        # 基本的な移動報酬
        velocity = current_x - self.prev_x
        velocity_reward = 0.2 * velocity if velocity > 0 else -0.1 * abs(velocity)

        # 進捗報酬
        progress_ratio = current_x / self.goal_x
        progress_reward = 10 * progress_ratio ** 2

        # 停滞ペナルティ
        stagnation_factor = min(self.stagnation_count / self.max_stagnation, 1.0)
        time_penalty = -0.1 * (1.0 + stagnation_factor)

        # ジャンプ報酬
        jump_reward = 0.5 if player_obj.isJump and not player_obj.isGrounding else 0

        # 地面接地ボーナス
        grounding_bonus = 1.0 if player_obj.isGrounding else 0

        # ゴール報酬
        if current_x >= self.goal_x:
            goal_bonus = self.goal_bonus
        elif current_x > self.goal_x * 0.9:
            goal_bonus = self.goal_bonus * 0.7
        else:
            goal_bonus = 0
        
        total_reward = (
            velocity_reward +
            progress_reward +
            time_penalty +
            jump_reward +
            grounding_bonus +
            goal_bonus
        )
        
        # 報酬のクリッピング
        total_reward = np.clip(total_reward, -20, 100)
        
        self.prev_x = current_x
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
