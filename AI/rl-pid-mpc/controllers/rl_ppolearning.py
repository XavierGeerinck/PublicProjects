import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical, Normal
from gymnasium import spaces


class PPOPolicy(nn.Module):
    """Neural network policy for PPO algorithm"""

    def __init__(self, obs_dim, action_dim, continuous=False, hidden_dim=64):
        super(PPOPolicy, self).__init__()

        # Shared network layers
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )

        self.continuous = continuous

        # Policy head (actor)
        if continuous:
            self.mean = nn.Linear(hidden_dim, action_dim)
            self.log_std = nn.Parameter(torch.zeros(action_dim))
        else:
            self.policy = nn.Linear(hidden_dim, action_dim)

        # Value head (critic)
        self.value = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        """Forward pass through network"""
        if isinstance(x, np.ndarray):
            x = torch.FloatTensor(x)

        shared_features = self.shared(x)

        # Value estimate
        value = self.value(shared_features)

        # Action distribution
        if self.continuous:
            action_mean = self.mean(shared_features)
            action_std = torch.exp(self.log_std)
            dist = Normal(action_mean, action_std)
        else:
            logits = self.policy(shared_features)
            dist = Categorical(logits=logits)

        return dist, value


class PPOAgent:
    def __init__(
        self,
        action_space,
        observation_space,
        learning_rate=3e-4,
        gamma=0.99,
        clip_ratio=0.2,
        value_coef=0.5,
        entropy_coef=0.01,
        update_epochs=4,
        batch_size=64,
    ):
        """
        Initialize PPO Agent compatible with Gymnasium environments

        Args:
            action_space: Gymnasium action space
            observation_space: Gymnasium observation space
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            clip_ratio: PPO clipping parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy coefficient for exploration
            update_epochs: Number of epochs to update policy per batch
            batch_size: Batch size for updates
        """
        self.action_space = action_space
        self.observation_space = observation_space

        # PPO hyperparameters
        self.gamma = gamma
        self.clip_ratio = clip_ratio
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.update_epochs = update_epochs
        self.batch_size = batch_size

        # Determine if action space is continuous
        self.continuous = isinstance(action_space, spaces.Box)

        # Get dimensions of observation and action spaces
        if isinstance(observation_space, spaces.Box):
            self.obs_dim = int(np.prod(observation_space.shape))
        else:
            self.obs_dim = observation_space.n

        if self.continuous:
            self.action_dim = action_space.shape[0]
        else:
            self.action_dim = action_space.n

        # Initialize policy network
        self.policy = PPOPolicy(self.obs_dim, self.action_dim, self.continuous)

        # Initialize optimizer
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)

        # Memory buffers for training
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []

    def _process_state(self, state):
        """Process state for network input"""
        if isinstance(state, np.ndarray):
            return state.flatten()
        return state

    def select_action(self, state):
        """Select action based on current policy"""
        state = self._process_state(state)

        # Get action distribution and value
        with torch.no_grad():
            dist, value = self.policy(state)

            # Sample action from distribution
            action = dist.sample()
            log_prob = dist.log_prob(action)

            # If continuous, we need to sum log probs across dimensions
            if self.continuous:
                log_prob = log_prob.sum()

        # Convert to numpy for environment
        if self.continuous:
            action_np = action.numpy()
            # Clip to action space bounds
            action_np = np.clip(
                action_np, self.action_space.low, self.action_space.high
            )
        else:
            action_np = action.item()

        return action_np

    def choose_action(self, state):
        """Alias for select_action method"""
        return self.select_action(state)

    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in memory buffer"""
        state = self._process_state(state)

        with torch.no_grad():
            dist, value = self.policy(state)

            # Get log probability of the action
            if self.continuous:
                action_tensor = torch.FloatTensor(action)
                log_prob = dist.log_prob(action_tensor).sum()
            else:
                action_tensor = torch.tensor(action)
                log_prob = dist.log_prob(action_tensor)

        # Store in memory
        self.states.append(state)
        self.actions.append(action)
        self.log_probs.append(log_prob.item())
        self.rewards.append(reward)
        self.values.append(value.item())
        self.dones.append(done)

    def compute_returns(self):
        """Compute returns and advantages"""
        # Calculate returns and advantages
        returns = []
        advantages = []

        next_value = 0
        next_advantage = 0

        for t in reversed(range(len(self.rewards))):
            # If episode terminates, reset values
            if self.dones[t]:
                next_return = 0
                next_advantage = 0

            # Compute return (discounted sum of rewards)
            next_return = self.rewards[t] + self.gamma * next_value * (
                1 - self.dones[t]
            )

            # Compute advantage (TD error)
            next_advantage = next_return - self.values[t]

            returns.insert(0, next_return)
            advantages.insert(0, next_advantage)

            next_value = self.values[t]

        return returns, advantages

    def update_policy(self):
        """Update policy using PPO algorithm"""
        # Compute returns and advantages
        returns, advantages = self.compute_returns()

        # Convert lists to tensors
        states = torch.FloatTensor(np.array(self.states))
        if self.continuous:
            actions = torch.FloatTensor(np.array(self.actions))
        else:
            actions = torch.LongTensor(np.array(self.actions))
        old_log_probs = torch.FloatTensor(self.log_probs)
        returns = torch.FloatTensor(returns)
        advantages = torch.FloatTensor(advantages)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO update
        for _ in range(self.update_epochs):
            # Generate random indices
            indices = np.arange(len(states))
            np.random.shuffle(indices)

            # Update in mini-batches
            for start in range(0, len(states), self.batch_size):
                end = start + self.batch_size
                idx = indices[start:end]

                # Get mini-batch
                mb_states = states[idx]
                mb_actions = actions[idx]
                mb_old_log_probs = old_log_probs[idx]
                mb_returns = returns[idx]
                mb_advantages = advantages[idx]

                # Get current policy outputs
                dist, values = self.policy(mb_states)

                # Get log probabilities of actions
                if self.continuous:
                    new_log_probs = dist.log_prob(mb_actions).sum(1)
                else:
                    new_log_probs = dist.log_prob(mb_actions)

                # Calculate ratios
                ratios = torch.exp(new_log_probs - mb_old_log_probs)

                # Calculate surrogate losses
                surr1 = ratios * mb_advantages
                surr2 = (
                    torch.clamp(ratios, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio)
                    * mb_advantages
                )

                # Calculate policy loss
                policy_loss = -torch.min(surr1, surr2).mean()

                # Calculate value loss
                value_loss = F.mse_loss(values.squeeze(), mb_returns)

                # Calculate entropy
                entropy = dist.entropy().mean()

                # Calculate total loss
                loss = (
                    policy_loss
                    + self.value_coef * value_loss
                    - self.entropy_coef * entropy
                )

                # Update policy
                self.optimizer.zero_grad()
                loss.backward()
                # Optional: gradient clipping
                # nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                self.optimizer.step()

        # Clear memory after update
        self.clear_memory()

        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": entropy.item(),
        }

    def clear_memory(self):
        """Clear memory buffers"""
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []

    def learn(self, state, action, reward, next_state, done=False):
        """Interface method to match Q-learning API"""
        self.store_transition(state, action, reward, next_state, done)

        # Only update policy after collecting enough transitions
        if done and len(self.states) >= self.batch_size:
            return self.update_policy()
        return None

    def save_model(self, filepath):
        """Save model to file"""
        torch.save(
            {
                "policy_state_dict": self.policy.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            filepath,
        )
        print(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """Load model from file"""
        try:
            checkpoint = torch.load(filepath)
            self.policy.load_state_dict(checkpoint["policy_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            print(f"Model loaded from {filepath}")
        except FileNotFoundError:
            print(f"Model file {filepath} not found. Starting with new model.")


# Example usage with a Gymnasium environment:
# import gymnasium as gym
# env = gym.make('CartPole-v1')
# ppo_agent = PPOAgent(env.action_space, env.observation_space)
