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
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, epsilon=0.2, epochs=10):
        self.policy = PolicyNetwork(state_dim, action_dim)
        self.value = ValueNetwork(state_dim)
        self.optimizer = optim.Adam(list(self.policy.parameters()) + list(self.value.parameters()), lr=lr)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epochs = epochs

    def act(self, state):
        state = torch.FloatTensor(state)
        probs = self.policy(state)
        dist = Categorical(probs)
        action = dist.sample()
        return action.item()

    def update(self, states, actions, rewards, dones):
        states = torch.FloatTensor(np.array(states))
        actions = torch.FloatTensor(actions)
        rewards = torch.FloatTensor(rewards)
        dones = torch.FloatTensor(dones)

        for _ in range(self.epochs):
            # 古いポリシーの確率を計算
            old_probs = self.policy(states).gather(1, actions.long().unsqueeze(1))
            old_values = self.value(states)

            # アドバンテージを計算
            returns = self.compute_returns(rewards, dones)
            advantages = returns - old_values

            # 新しいポリシーの確率を計算
            new_probs = self.policy(states).gather(1, actions.long().unsqueeze(1))
            new_values = self.value(states)

            # ポリシーの損失を計算
            ratio = new_probs / old_probs
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            # バリューネットワークの損失を計算
            value_loss = nn.MSELoss()(new_values, returns)

            # 全体の損失
            loss = policy_loss + value_loss

            # バックプロパゲーション
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def compute_returns(self, rewards, dones):
        returns = []
        R = 0
        for reward, done in zip(reversed(rewards), reversed(dones)):
            R = reward + self.gamma * R * (1 - done)
            returns.insert(0, R)
        returns = torch.FloatTensor(returns)
        returns = returns.unsqueeze(1)  # 形状を [63] → [63, 1] に変換
        return returns
