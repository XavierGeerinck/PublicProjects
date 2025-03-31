import random
import numpy as np
from gymnasium import spaces


class QLearningAgent:
    def __init__(
        self, action_space, observation_space, alpha=0.1, gamma=0.9, epsilon=0.1
    ):
        """
        Initialize Q-Learning agent compatible with Gymnasium environments

        Args:
            action_space: Gymnasium action space
            observation_space: Gymnasium observation space
            alpha: Learning rate
            gamma: Discount factor
            epsilon: Exploration rate
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_values = {}

        # Handle Gymnasium spaces
        self.action_space = action_space
        self.observation_space = observation_space

        # Get list of valid actions based on space type
        if isinstance(action_space, spaces.Discrete):
            self.actions = list(range(action_space.n))
        else:
            raise ValueError("Only Discrete action spaces are supported")

    def _process_state(self, state):
        """Convert state to hashable representation"""
        if isinstance(state, np.ndarray):
            return tuple(state.flatten())
        else:
            return tuple(state)

    def get_q_value(self, state, action):
        """Get Q-value for a state-action pair"""
        state = self._process_state(state)
        return self.q_values.get((state, action), 0.0)

    def update_q_value(self, state, action, value):
        """Update Q-value for a state-action pair"""
        state = self._process_state(state)
        self.q_values[(state, action)] = value

    def choose_action(self, state):
        """Choose action using epsilon-greedy policy"""
        if random.random() < self.epsilon:
            return self.action_space.sample()  # Use Gymnasium's sample method
        else:
            return self.get_best_action(state)

    def get_best_action(self, state):
        """Get the best action for the current state"""
        q_values = [self.get_q_value(state, a) for a in self.actions]
        max_q = max(q_values)

        # Handle multiple actions with the same max value
        best_actions = [a for a, q in zip(self.actions, q_values) if q == max_q]
        return random.choice(best_actions)

    def select_action(self, state):
        """Select action using the best action policy"""
        return self.get_best_action(state)

    def learn(self, state, action, reward, next_state, done=False):
        """Update Q-values using the Q-learning update rule"""
        q_current = self.get_q_value(state, action)

        # Terminal state handling
        if done:
            q_target = reward
        else:
            # Max Q-value for next state
            next_q_values = [self.get_q_value(next_state, a) for a in self.actions]
            q_target = reward + self.gamma * max(next_q_values)

        # Q-learning update rule
        new_q_value = q_current + self.alpha * (q_target - q_current)
        self.update_q_value(state, action, new_q_value)

    def decay_epsilon(self, decay_rate=0.995, min_epsilon=0.01):
        """Decay exploration rate"""
        self.epsilon = max(min_epsilon, self.epsilon * decay_rate)

    def save_q_table(self, filepath):
        """Save Q-table to file"""
        with open(filepath, "w") as f:
            for (state, action), value in self.q_values.items():
                f.write(f"{state},{action},{value}\n")

    def load_q_table(self, filepath):
        """Load Q-table from file"""
        try:
            with open(filepath, "r") as f:
                for line in f:
                    state_str, action_str, value_str = line.strip().split(",", 2)
                    state = eval(state_str)
                    action = int(action_str)
                    value = float(value_str)
                    self.q_values[(state, action)] = value
        except FileNotFoundError:
            print(f"Q-table file {filepath} not found. Starting with empty Q-table.")


# Example usage with a Gymnasium environment:
# import gymnasium as gym
# env = gym.make('CartPole-v1')
# rl_agent = QLearningAgent(env.action_space, env.observation_space)
