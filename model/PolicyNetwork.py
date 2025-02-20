import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical


class PolicyNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(PolicyNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        return self.fc(x)


class ValueNetwork(nn.Module):
    def __init__(self, input_dim):
        super(ValueNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        return self.fc(x)


class PPO:
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, epsilon=0.2, ent_coef=0.01, epochs=10):
        self.policy = PolicyNetwork(state_dim, action_dim)
        self.value = ValueNetwork(state_dim)
        self.optimizer = optim.Adam(list(self.policy.parameters()) + list(self.value.parameters()), lr=lr)
        self.gamma = gamma
        self.epsilon = epsilon
        self.ent_coef = ent_coef
        self.epochs = epochs
        self.episode_count = 0
        self.action_dim = action_dim

    def act(self, state):
        state = torch.FloatTensor(state)
        probs = self.policy(state)
        dist = Categorical(probs)
        action = dist.sample()
        return action.item()

    def update(self, states, actions, rewards, dones):
        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)

        # GAEの導入
        with torch.no_grad():
            values = self.value(states)
            next_value = 0
            advantages = []
            returns = []

            # 逆順で計算
            for t in reversed(range(len(rewards))):
                delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
                advantages.insert(0, delta + self.gamma * 0.95 * (1 - dones[t]) * (
                    advantages[0] if len(advantages) > 0 else 0))
                next_value = values[t]
                returns.insert(0, advantages[0] + values[t])

            old_probs = self.policy(states).gather(1, actions.unsqueeze(1))
            advantages = torch.FloatTensor(advantages)
            returns = torch.FloatTensor(returns)
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        for _ in range(self.epochs):
            # 新しい確率と価値を計算
            new_probs = self.policy(states).gather(1, actions.unsqueeze(1))
            new_values = self.value(states)

            # エントロピー計算
            entropy = -torch.sum(new_probs * torch.log(new_probs + 1e-8), dim=1).mean()

            # ポリシー損失の計算
            ratio = new_probs / old_probs
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean() - self.ent_coef * entropy

            # バリュー損失の計算
            value_loss = nn.MSELoss()(new_values, returns)

            # 結合損失
            loss = policy_loss + value_loss

            # 最適化
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def compute_returns(self, rewards, dones):
        returns = []
        R = 0
        for reward, done in zip(reversed(rewards), reversed(dones)):
            R = reward + self.gamma * R * (1 - done.item())
            returns.insert(0, R)
        return torch.FloatTensor(returns).unsqueeze(1)


class SimpleRewardSystem:
    goal_x = 3477 + 210
    prev_x = 0  # 前ステップの位置
    current_x = 0  # 現在の位置
    delta_x = 0  # 位置変化量
    stagnation_count = 0  # 連続停滞カウンタ
    episode_count = 0
    max_stagnation = 50  # 最大停滞フレーム数

    @classmethod
    def calculate_reward(cls, current_x):
        # 速度ベースの報酬（前フレームとの差分）
        velocity = current_x - cls.prev_x
        velocity_reward = 0.1 * velocity if velocity > 0 else 0.5 * velocity  # 後退は強いペナルティ

        # 進捗報酬（非線形設計）
        progress_ratio = current_x / cls.goal_x
        progress_reward = 10 * progress_ratio ** 2

        stagnation_factor = min(cls.stagnation_count / cls.max_stagnation, 1.0)
        time_penalty = -0.1 * (1.0 + 2.0 * stagnation_factor)

        # ゴール報酬（段階的ボーナス）
        if current_x >= cls.goal_x:
            goal_bonus = 100.0
        elif current_x > cls.goal_x * 0.9:
            goal_bonus = 50.0
        else:
            goal_bonus = 0

        total_reward = (
                velocity_reward +
                progress_reward +
                time_penalty +
                goal_bonus
        )

        # デバッグ用ログ
        # print(f"VR: {velocity_reward:.2f}, PR: {progress_reward:.2f}, "
        #       f"TP: {time_penalty:.2f}, GB: {goal_bonus:.2f}")

        return total_reward, (current_x >= cls.goal_x)

    @classmethod
    def update_episode(cls, episode_count):
        cls.delta_x = cls.current_x - cls.prev_x

        # 停滞カウント更新
        if abs(cls.delta_x) < 10:
            cls.stagnation_count += 1
        else:
            cls.stagnation_count = 0

        print("stagnation_count: ", cls.stagnation_count)

        cls.prev_x = cls.current_x
        cls.episode_count = episode_count

    @classmethod
    def reset(cls):
        cls.prev_x = 0  # 前ステップの位置
        cls.current_x = 0  # 現在の位置
        cls.delta_x = 0  # 位置変化量
        cls.stagnation_count = 0  # 連続停滞カウンタ
        cls.episode_count = 0
