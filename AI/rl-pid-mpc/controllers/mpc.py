import numpy as np
from scipy.optimize import minimize


class MPCController:
    def __init__(
        self,
        action_space,
        observation_space,
        prediction_horizon=10,
        dt=0.02,
        Q=None,  # State cost weights
        R=None,  # Control cost weight
        target_state=None,
    ):
        """
        Initialize MPC controller compatible with Gymnasium environments

        Args:
            action_space: Gymnasium action space
            observation_space: Gymnasium observation space
            prediction_horizon: Number of steps to predict into the future
            dt: Time step for discretization
            Q: State cost weights [x, x_dot, theta, theta_dot]
            R: Control cost weight (penalty on control effort)
            target_state: Target state vector [x, x_dot, theta, theta_dot]
        """
        self.action_space = action_space
        self.observation_space = observation_space
        self.prediction_horizon = prediction_horizon
        self.dt = dt

        # Get dimensions from spaces
        if hasattr(observation_space, "shape"):
            self.state_dim = observation_space.shape[0]  # Typically 4 for CartPole
        else:
            self.state_dim = 4  # Default for CartPole: [x, x_dot, theta, theta_dot]

        # Default target state: upright pole at center
        if target_state is None:
            self.target_state = np.zeros(self.state_dim)
        else:
            self.target_state = np.array(target_state)

        # Default cost weights if not provided
        if Q is None:
            # Higher weights on pole angle and angular velocity for stability
            self.Q = np.array([1.0, 0.1, 10.0, 1.0])
        else:
            self.Q = np.array(Q)

        if R is None:
            self.R = 0.1  # Default control cost
        else:
            self.R = R

        # Get action bounds from action space
        if hasattr(action_space, "low") and hasattr(action_space, "high"):
            self.action_low = action_space.low
            self.action_high = action_space.high
        else:
            # Default bounds if not available
            self.action_low = -1.0
            self.action_high = 1.0

        # If action limits are arrays, we'll use the first element
        if isinstance(self.action_low, np.ndarray):
            self.action_low = self.action_low[0]
        if isinstance(self.action_high, np.ndarray):
            self.action_high = self.action_high[0]

        # System parameters for CartPole
        self.gravity = 9.8
        self.masscart = 1.0
        self.masspole = 0.1
        self.total_mass = self.masscart + self.masspole
        self.length = 0.5  # half the pole's length
        self.polemass_length = self.masspole * self.length

        # Last optimal action sequence for warm start
        self.last_optimal_sequence = None

    def cartpole_dynamics(self, state, action):
        """
        CartPole dynamics model for prediction

        Args:
            state: Current state [x, x_dot, theta, theta_dot]
            action: Control input (force)

        Returns:
            Next state after applying dynamics
        """
        # Unpack state
        x, x_dot, theta, theta_dot = state

        # Clip action to valid range
        action = np.clip(action, self.action_low, self.action_high)

        # Compute acceleration
        force = action
        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        # Equations from the CartPole dynamics
        temp = (
            force + self.polemass_length * theta_dot**2 * sintheta
        ) / self.total_mass
        thetaacc = (self.gravity * sintheta - costheta * temp) / (
            self.length * (4.0 / 3.0 - self.masspole * costheta**2 / self.total_mass)
        )
        xacc = temp - self.polemass_length * thetaacc * costheta / self.total_mass

        # Euler integration
        x_new = x + self.dt * x_dot
        x_dot_new = x_dot + self.dt * xacc
        theta_new = theta + self.dt * theta_dot
        theta_dot_new = theta_dot + self.dt * thetaacc

        return np.array([x_new, x_dot_new, theta_new, theta_dot_new])

    def simulate_trajectory(self, initial_state, action_sequence):
        """
        Simulate the system trajectory for a given action sequence

        Args:
            initial_state: Initial state [x, x_dot, theta, theta_dot]
            action_sequence: Sequence of control actions

        Returns:
            Predicted state trajectory
        """
        states = [initial_state]
        current_state = initial_state.copy()

        for action in action_sequence:
            next_state = self.cartpole_dynamics(current_state, action)
            states.append(next_state)
            current_state = next_state

        return np.array(states)

    def compute_cost(self, action_sequence, initial_state):
        """
        Compute total cost for a given action sequence and initial state

        Args:
            action_sequence: Sequence of control actions
            initial_state: Initial state

        Returns:
            Total cost (scalar)
        """
        # Simulate trajectory
        states = self.simulate_trajectory(initial_state, action_sequence)

        # Compute state costs
        state_costs = 0
        for i in range(1, len(states)):  # Skip initial state
            state_error = states[i] - self.target_state
            state_costs += np.sum(self.Q * state_error**2)

        # Compute control costs
        control_costs = 0
        for action in action_sequence:
            control_costs += self.R * action**2

        return state_costs + control_costs

    def select_action(self, state):
        """
        Compute the optimal action using Model Predictive Control

        Args:
            state: Current state observation

        Returns:
            Optimal action to take
        """
        # Ensure state is a numpy array
        if not isinstance(state, np.ndarray):
            state = np.array(state)

        # Initialize guess for optimization
        if self.last_optimal_sequence is not None:
            # Warm start: shift previous solution and append a zero
            initial_guess = np.append(self.last_optimal_sequence[1:], 0.0)
        else:
            initial_guess = np.zeros(self.prediction_horizon)

        # Define bounds for all actions
        bounds = [(self.action_low, self.action_high)] * self.prediction_horizon

        # Solve the optimization problem
        result = minimize(
            self.compute_cost,
            initial_guess,
            args=(state,),
            method="SLSQP",
            bounds=bounds,
            options={"maxiter": 50, "disp": False},
        )

        # Extract optimal action sequence
        if result.success:
            optimal_sequence = result.x
            self.last_optimal_sequence = optimal_sequence
        else:
            # Fallback if optimization fails
            if self.last_optimal_sequence is not None:
                optimal_sequence = np.append(self.last_optimal_sequence[1:], 0.0)
            else:
                optimal_sequence = np.zeros(self.prediction_horizon)

        # Apply only the first action from the sequence (receding horizon principle)
        optimal_action = optimal_sequence[0]

        # For discrete action spaces (like CartPole-v1)
        if hasattr(self.action_space, "n"):
            # Convert continuous action to discrete (0 or 1 for CartPole)
            return 1 if optimal_action > 0 else 0
        else:
            # For continuous action spaces
            return np.clip(optimal_action, self.action_low, self.action_high)

    def reset(self):
        """Reset controller state"""
        self.last_optimal_sequence = None

    def update_parameters(
        self, prediction_horizon=None, dt=None, Q=None, R=None, target_state=None
    ):
        """
        Update MPC controller parameters

        Args:
            prediction_horizon: New prediction horizon
            dt: New time step
            Q: New state cost weights
            R: New control cost weight
            target_state: New target state
        """
        if prediction_horizon is not None:
            self.prediction_horizon = prediction_horizon
            self.last_optimal_sequence = None  # Reset when horizon changes
        if dt is not None:
            self.dt = dt
        if Q is not None:
            self.Q = np.array(Q)
        if R is not None:
            self.R = R
        if target_state is not None:
            self.target_state = np.array(target_state)
