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
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, epsilon=0.2, ent_coef=0.01, epochs=10):
        self.policy = PolicyNetwork(state_dim, action_dim)
        self.value = ValueNetwork(state_dim)
        self.optimizer = optim.Adam(list(self.policy.parameters()) + list(self.value.parameters()), lr=lr)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=100, gamma=0.9)
        
        self.gamma = gamma
        self.epsilon = epsilon
        self.ent_coef = ent_coef
        self.epochs = epochs
        self.action_dim = action_dim
        
        # バッファ関連
        self.buffer_size = 2048
        self.batch_size = 64
        self.clear_buffers()
        
        # 学習の安定化のためのパラメータ
        self.max_grad_norm = 0.5
        self.value_loss_coef = 0.5
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy.to(self.device)
        self.value.to(self.device)

    def clear_buffers(self):
        self.states_buffer = []
        self.actions_buffer = []
        self.rewards_buffer = []
        self.dones_buffer = []
        self.values_buffer = []
        self.returns_buffer = []
        self.advantages_buffer = []

    def act(self, state):
        with torch.no_grad():
            state = torch.FloatTensor(state).to(self.device)
            probs = self.policy(state)
            dist = Categorical(probs)
            action = dist.sample()
            value = self.value(state)
            
            self.states_buffer.append(state.cpu().numpy())
            self.actions_buffer.append(action.item())
            self.values_buffer.append(value.item())
            
            return action.item()

    def compute_gae(self, rewards, values, dones, next_value):
        gae = 0
        returns = []
        advantages = []
        
        for step in reversed(range(len(rewards))):
            if step == len(rewards) - 1:
                next_non_terminal = 1.0 - dones[step]
                next_value = next_value
            else:
                next_non_terminal = 1.0 - dones[step]
                next_value = values[step + 1]
                
            delta = rewards[step] + self.gamma * next_value * next_non_terminal - values[step]
            gae = delta + self.gamma * 0.95 * next_non_terminal * gae
            
            returns.insert(0, gae + values[step])
            advantages.insert(0, gae)
            
        return returns, advantages

    def update(self):
        if len(self.states_buffer) < self.buffer_size:
            return

        # バッファデータの準備
        states = torch.FloatTensor(np.array(self.states_buffer)).to(self.device)
        actions = torch.LongTensor(self.actions_buffer).to(self.device)
        rewards = torch.FloatTensor(self.rewards_buffer).to(self.device)
        dones = torch.FloatTensor(self.dones_buffer).to(self.device)
        values = torch.FloatTensor(self.values_buffer).to(self.device)
        
        # GAEの計算
        with torch.no_grad():
            next_value = self.value(states[-1]).item()
            returns, advantages = self.compute_gae(rewards, values, dones, next_value)
            
        returns = torch.FloatTensor(returns).to(self.device)
        advantages = torch.FloatTensor(advantages).to(self.device)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # データローダーの作成
        dataset = TensorDataset(states, actions, returns, advantages)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # 複数エポックで学習
        for _ in range(self.epochs):
            for batch_states, batch_actions, batch_returns, batch_advantages in dataloader:
                # 新しい行動確率と価値の計算
                new_probs = self.policy(batch_states)
                new_values = self.value(batch_states)
                dist = Categorical(new_probs)
                
                # エントロピーの計算
                entropy = dist.entropy().mean()
                
                # 行動の対数確率
                log_probs = dist.log_prob(batch_actions)
                old_log_probs = dist.log_prob(batch_actions).detach()
                
                # レシオの計算
                ratio = torch.exp(log_probs - old_log_probs)
                
                # PPOクリップ
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # 価値損失
                value_loss = 0.5 * (batch_returns - new_values.squeeze()).pow(2).mean()
                
                # 全体の損失
                loss = policy_loss + self.value_loss_coef * value_loss - self.ent_coef * entropy
                
                # 最適化
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                torch.nn.utils.clip_grad_norm_(self.value.parameters(), self.max_grad_norm)
                self.optimizer.step()
        
        self.scheduler.step()
        self.clear_buffers()


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
