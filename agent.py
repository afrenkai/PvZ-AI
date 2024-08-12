import random
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from collections import deque

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size  # Size of the state space (observation space)
        self.action_size = action_size  # Size of the action space
        self.memory = deque(maxlen=2000)  # Experience replay memory
        self.gamma = 0.95  # Discount factor for future rewards
        self.epsilon = 1.0  # Initial exploration rate
        self.epsilon_min = 0.01  # Minimum exploration rate
        self.epsilon_decay = 0.995  # Decay rate for exploration
        self.learning_rate = 0.001  # Learning rate for the optimizer
        self.model = self._build_model()  # The Q-network

    def _build_model(self):
        """Build the Deep Q-Network."""
        model = tf.keras.Sequential()
        model.add(layers.Dense(24, input_dim=self.state_size, activation='relu'))  # Input layer
        model.add(layers.Dense(24, activation='relu'))  # Hidden layer
        model.add(layers.Dense(self.action_size, activation='linear'))  # Output layer
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        """Store experiences in replay memory."""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """Choose an action based on the current state."""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)  # Explore: random action
        act_values = self.model.predict(state)  # Predict Q-values for the current state
        return np.argmax(act_values[0])  # Exploit: action with the highest Q-value

    def replay(self, batch_size):
        """Train the model using randomly sampled experiences from memory."""
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        """Load the model weights from a file."""
        self.model.load_weights(name)

    def save(self, name):
        """Save the model weights to a file."""
        self.model.save_weights(name)
