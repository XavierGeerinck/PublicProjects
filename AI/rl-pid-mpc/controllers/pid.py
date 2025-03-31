import numpy as np


class PIDController:
    def __init__(
        self, action_space, observation_space, Kp=1.0, Ki=0.1, Kd=0.05, setpoint=0.0
    ):
        """
        Initialize PID controller compatible with Gymnasium environments

        Args:
            action_space: Gymnasium action space
            observation_space: Gymnasium observation space
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
            setpoint: Target value for the controlled variable
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.last_error = 0.0
        self.setpoint = setpoint

        # Get action bounds from action space
        self.action_space = action_space
        self.observation_space = observation_space

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

    def control(self, error, dt=1.0):
        """
        Compute PID control output based on error

        Args:
            error: Difference between setpoint and measured value
            dt: Time step since last control update

        Returns:
            Control output
        """
        # Proportional term
        p_term = self.Kp * error

        # Integral term - accumulate error
        self.integral += error * dt
        i_term = self.Ki * self.integral

        # Derivative term - rate of change of error
        derivative = (error - self.last_error) / dt
        d_term = self.Kd * derivative

        # Save error for next iteration
        self.last_error = error

        # Sum the terms
        output = p_term + i_term + d_term

        # Clamp output to action space limits
        output = max(self.action_low, min(self.action_high, output))

        return output

    def reset(self):
        """Reset integral and error history"""
        self.integral = 0.0
        self.last_error = 0.0

    def select_action(self, state):
        """
        Interface method to match other controllers

        Args:
            state: Current state observation

        Returns:
            Action to take
        """
        # For a simple case, assume the first state variable is the one we want to control
        # In real applications, you may need more complex logic to compute the error
        if isinstance(state, np.ndarray):
            measured_value = state[0]  # Assuming first value is what we control
        else:
            measured_value = state

        error = self.setpoint - measured_value
        return self.control(error)

    def update_parameters(self, Kp=None, Ki=None, Kd=None, setpoint=None):
        """
        Update PID controller parameters

        Args:
            Kp: New proportional gain (or None to keep current)
            Ki: New integral gain (or None to keep current)
            Kd: New derivative gain (or None to keep current)
            setpoint: New setpoint (or None to keep current)
        """
        if Kp is not None:
            self.Kp = Kp
        if Ki is not None:
            self.Ki = Ki
        if Kd is not None:
            self.Kd = Kd
        if setpoint is not None:
            self.setpoint = setpoint


# Example usage with a Gymnasium environment:
# import gymnasium as gym
# env = gym.make('CartPole-v1')
# pid_controller = PIDController(env.action_space, env.observation_space, Kp=2.0, Ki=0.2, Kd=0.1)
