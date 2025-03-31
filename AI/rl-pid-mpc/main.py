import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import imageio
import os
import multiprocessing as mp
from functools import partial
import time

from controllers.pid import PIDController
from controllers.mpc import MPCController

# from controllers.rl_qlearning import QLearningAgent
from controllers.rl_ppolearning import PPOAgent

# Create output directory if it doesn't exist
os.makedirs("results", exist_ok=True)

# Create the CartPole environment
env = gym.make("CartPole-v1", render_mode="rgb_array")

# Initialize controllers
pid_controller = PIDController(
    env.action_space, env.observation_space, Kp=1.0, Ki=0.05, Kd=0.5, setpoint=0.0
)
mpc_controller = MPCController(
    env.action_space, env.observation_space, prediction_horizon=10
)
rl_agent = PPOAgent(
    env.action_space,
    env.observation_space,
    learning_rate=3e-4,
    gamma=0.99,
    clip_ratio=0.2,
)


# Function to run an episode with a given controller
def run_episode(controller, max_steps=500):
    state, _ = env.reset()
    total_reward = 0
    frames = []
    done = False
    step = 0

    while not done and step < max_steps:
        # Use the unified select_action interface for all controllers
        action = controller.select_action(state)

        # Convert continuous actions to discrete for CartPole
        if not isinstance(action, int):
            action = 0 if action < 0 else 1

        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        total_reward += reward
        frames.append(env.render())

        state = next_state
        step += 1

    return frames, total_reward


def save_gif(frames, filename):
    """Save frames as a GIF"""
    imageio.mimsave(f"results/{filename}", frames, fps=30)
    print(f"Saved {filename}")


def train_rl_agent(agent, episodes=1000):
    """Train the RL agent"""
    rewards = []

    for episode in range(episodes):
        state, _ = env.reset()
        episode_reward = 0
        done = False

        while not done:
            action = agent.choose_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            agent.learn(state, action, reward, next_state, done)
            state = next_state
            episode_reward += reward

        rewards.append(episode_reward)
        if episode % 100 == 0:
            print(f"RL Episode {episode}/{episodes}, Reward: {episode_reward}")

    return rewards


def train_mpc_controller(controller, episodes=50):
    """Train or tune the MPC controller (simplified for demo)"""
    rewards = []

    for episode in range(episodes):
        state, _ = env.reset()
        episode_reward = 0
        done = False

        while not done:
            action = controller.select_action(state)
            # Convert to discrete action for CartPole
            action = 0 if action < 0 else 1

            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            state = next_state
            episode_reward += reward

        rewards.append(episode_reward)
        if episode % 10 == 0:
            print(f"MPC Episode {episode}/{episodes}, Reward: {episode_reward}")

    return rewards


def tune_pid_controller(controller, episodes=50):
    """Find good PID parameters through brief testing"""
    best_reward = 0
    best_params = (controller.Kp, controller.Ki, controller.Kd)
    pid_rewards = []

    # Try different PID parameters
    for kp in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]:
        for ki in [0.0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.150, 0.175, 0.2]:
            for kd in [0.1, 0.25, 0.5, 0.75, 1.0]:
                controller.update_parameters(Kp=kp, Ki=ki, Kd=kd)

                # Test with these parameters
                total_reward = 0
                for _ in range(5):  # 5 episodes per parameter set
                    _, episode_reward = run_episode(controller)
                    total_reward += episode_reward

                avg_reward = total_reward / 5
                print(
                    f"PID params: Kp={kp}, Ki={ki}, Kd={kd}, Avg reward: {avg_reward}"
                )

                pid_rewards.append((kp, ki, kd, avg_reward))

                if avg_reward > best_reward:
                    best_reward = avg_reward
                    best_params = (kp, ki, kd)

    # Set the best parameters
    controller.update_parameters(
        Kp=best_params[0], Ki=best_params[1], Kd=best_params[2]
    )
    print(
        f"Best PID parameters: Kp={best_params[0]}, Ki={best_params[1]}, Kd={best_params[2]}"
    )

    return pid_rewards


# Add this function after tune_pid_controller or where appropriate in your main.py
def plot_pid_grid_search_results(pid_rewards):
    """
    Create visualizations for PID grid search results

    Args:
        pid_rewards: List of tuples (kp, ki, kd, avg_reward)
    """
    # Convert list of tuples to arrays for easier plotting
    kp_values = np.array([x[0] for x in pid_rewards])
    ki_values = np.array([x[1] for x in pid_rewards])
    kd_values = np.array([x[2] for x in pid_rewards])
    rewards = np.array([x[3] for x in pid_rewards])

    # Find the best parameters
    best_idx = np.argmax(rewards)
    best_kp, best_ki, best_kd, best_reward = pid_rewards[best_idx]

    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(15, 10))

    # 1. 3D scatter plot of all parameters
    ax1 = fig.add_subplot(221, projection="3d")
    scatter = ax1.scatter(
        kp_values,
        ki_values,
        kd_values,
        c=rewards,
        cmap="viridis",
        s=rewards / 5,
        alpha=0.7,
    )
    ax1.set_xlabel("Kp")
    ax1.set_ylabel("Ki")
    ax1.set_zlabel("Kd")
    ax1.set_title("PID Parameter Space (color = reward)")
    fig.colorbar(scatter, ax=ax1, label="Average Reward")

    # Mark the best point
    ax1.scatter([best_kp], [best_ki], [best_kd], color="red", s=100, marker="*")

    # 2. Kp vs Reward (averaged over other parameters)
    ax2 = fig.add_subplot(222)
    kp_unique = sorted(list(set(kp_values)))
    kp_avg_rewards = [np.mean(rewards[kp_values == kp]) for kp in kp_unique]
    ax2.plot(kp_unique, kp_avg_rewards, "o-", linewidth=2)
    ax2.set_xlabel("Kp Value")
    ax2.set_ylabel("Average Reward")
    ax2.set_title("Effect of Kp on Reward")
    ax2.grid(True, alpha=0.3)

    # 3. Ki vs Reward (averaged over other parameters)
    ax3 = fig.add_subplot(223)
    ki_unique = sorted(list(set(ki_values)))
    ki_avg_rewards = [np.mean(rewards[ki_values == ki]) for ki in ki_unique]
    ax3.plot(ki_unique, ki_avg_rewards, "o-", linewidth=2)
    ax3.set_xlabel("Ki Value")
    ax3.set_ylabel("Average Reward")
    ax3.set_title("Effect of Ki on Reward")
    ax3.grid(True, alpha=0.3)

    # 4. Kd vs Reward (averaged over other parameters)
    ax4 = fig.add_subplot(224)
    kd_unique = sorted(list(set(kd_values)))
    kd_avg_rewards = [np.mean(rewards[kd_values == kd]) for kd in kd_unique]
    ax4.plot(kd_unique, kd_avg_rewards, "o-", linewidth=2)
    ax4.set_xlabel("Kd Value")
    ax4.set_ylabel("Average Reward")
    ax4.set_title("Effect of Kd on Reward")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/pid_grid_search_results.png", dpi=300)
    print("PID grid search visualization saved to results/pid_grid_search_results.png")

    # Additionally, create a heatmap of the best parameters for each Kp-Ki combination
    # (averaging over Kd values)
    plt.figure(figsize=(10, 8))
    unique_kp = np.sort(np.unique(kp_values))
    unique_ki = np.sort(np.unique(ki_values))

    # Create a 2D grid for the heatmap
    heatmap_data = np.zeros((len(unique_kp), len(unique_ki)))

    # Fill the grid with average rewards
    for i, kp in enumerate(unique_kp):
        for j, ki in enumerate(unique_ki):
            # Get rewards for this combination
            mask = (kp_values == kp) & (ki_values == ki)
            if np.any(mask):
                heatmap_data[i, j] = np.mean(rewards[mask])

    # Plot the heatmap
    plt.imshow(heatmap_data, cmap="viridis", aspect="auto", origin="lower")
    plt.colorbar(label="Average Reward")
    plt.xticks(
        np.arange(len(unique_ki)), [f"{ki:.3f}" for ki in unique_ki], rotation=45
    )
    plt.yticks(np.arange(len(unique_kp)), [f"{kp:.2f}" for kp in unique_kp])
    plt.xlabel("Ki Value")
    plt.ylabel("Kp Value")
    plt.title("PID Performance Heatmap (Kp vs Ki, averaged over Kd)")

    # Mark the best combination
    best_kp_idx = np.where(unique_kp == best_kp)[0][0]
    best_ki_idx = np.where(unique_ki == best_ki)[0][0]
    plt.plot(best_ki_idx, best_kp_idx, "r*", markersize=15)

    plt.tight_layout()
    plt.savefig("results/pid_param_heatmap.png", dpi=300)
    print("PID parameter heatmap saved to results/pid_param_heatmap.png")


# Create GIFs BEFORE training
print("Running untrained controllers...")

# print("Running untrained PID controller...")
# pid_frames_before, pid_reward_before = run_episode(pid_controller)
# save_gif(pid_frames_before, "pid_before_training.gif")
# print(f"PID reward before tuning: {pid_reward_before}")

print("Running untrained MPC controller...")
mpc_frames_before, mpc_reward_before = run_episode(mpc_controller)
save_gif(mpc_frames_before, "mpc_before_training.gif")
print(f"MPC reward before training: {mpc_reward_before}")

# print("Running untrained RL agent...")
# rl_frames_before, rl_reward_before = run_episode(rl_agent)
# save_gif(rl_frames_before, "rl_before_training.gif")
# print(f"RL reward before training: {rl_reward_before}")

# Train controllers
print("\nTraining controllers...")

# print("Tuning PID controller...")
# pid_rewards = tune_pid_controller(pid_controller)
# plot_pid_grid_search_results(pid_rewards)

print("Training MPC controller...")
mpc_rewards = train_mpc_controller(mpc_controller, episodes=1000)

# print("Training RL agent (PPO)...")
# rl_rewards = train_rl_agent(rl_agent, episodes=5000)

# Create GIFs AFTER training
print("\nRunning trained controllers...")

# print("Running tuned PID controller...")
# pid_frames_after, pid_reward_after = run_episode(pid_controller)
# save_gif(pid_frames_after, "pid_after_tuning.gif")
# print(f"PID reward after tuning: {pid_reward_after}")

print("Running trained MPC controller...")
mpc_frames_after, mpc_reward_after = run_episode(mpc_controller)
save_gif(mpc_frames_after, "mpc_after_training.gif")
print(f"MPC reward after training: {mpc_reward_after}")

# print("Running trained RL agent...")
# rl_frames_after, rl_reward_after = run_episode(rl_agent)
# save_gif(rl_frames_after, "rl_after_training.gif")
# print(f"RL reward after training: {rl_reward_after}")

# # Create comparison plot of learning curves
# plt.figure(figsize=(10, 6))
# plt.plot(range(len(rl_rewards)), rl_rewards, label="RL Agent")
# # plt.plot(range(len(mpc_rewards)), mpc_rewards, label="MPC Controller")
# plt.xlabel("Episode")
# plt.ylabel("Total Reward")
# plt.title("Learning Curves")
# plt.legend()
# plt.savefig("results/learning_curves.png")

# Create comparison plot of learning curves for PID
# this compares kp, ki, kd, avg_reward
# plt.figure(figsize=(10, 6))
# plt.plot(range(len(pid_rewards)), pid_rewards, label="PID Controller")
# plt.xlabel("Episode")
# plt.ylabel("Total Reward")
# plt.title("Learning Curves")
# plt.legend()
# plt.savefig("results/learning_curves-pid.png")


# Create comparison plot of learning curves
plt.figure(figsize=(10, 6))
plt.plot(range(len(mpc_rewards)), mpc_rewards, label="MPC Controller")
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("Learning Curves")
plt.legend()
plt.savefig("results/learning_curves-mpc.png")

# # Create comparison plot of learning curves
# plt.figure(figsize=(10, 6))
# plt.plot(range(len(rl_rewards)), rl_rewards, label="RL Agent")
# plt.xlabel("Episode")
# plt.ylabel("Total Reward")
# plt.title("Learning Curves")
# plt.legend()
# plt.savefig("results/learning_curves-rl.png")

# Print performance comparison
print("\nPerformance Comparison:")
# print(
#     f"PID Controller: Before={pid_reward_before}, After={pid_reward_after}, Improvement={pid_reward_after - pid_reward_before}"
# )
print(
    f"MPC Controller: Before={mpc_reward_before}, After={mpc_reward_after}, Improvement={mpc_reward_after - mpc_reward_before}"
)
# print(
#     f"RL Agent: Before={rl_reward_before}, After={rl_reward_after}, Improvement={rl_reward_after - rl_reward_before}"
# )

# Close the environment
env.close()
