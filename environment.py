import gym
from gym import spaces
import numpy as np
from logic import *


class PvZEnv(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, plants, zombies):
        super(PvZEnv, self).__init__()

        # Environment setup
        self.lanes = 5
        self.cols = 11  # Including home and lawnmower columns
        self.sun = 150  # Starting sun points
        self.game = Game(world=1, lanes=self.lanes, cols=self.cols, sun=self.sun)
        self.lawnmowers = [True] * self.lanes

        # Action space: (plant_index * num_lanes * num_cols) + (lane * num_cols) + col
        self.num_plants = len(plants)
        self.action_space = spaces.Discrete(self.num_plants * self.lanes * (self.cols - 2) + 1)

        # Observation space: Flattened field plus sun points
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.lanes * self.cols + 1,), dtype=np.float32)

        # Store plants and zombies information
        self.plants = list(plants.values())
        self.zombies = zombies

    def reset(self):
        """Reset the game to the initial state"""
        self.game = Game(world=1, lanes=self.lanes, cols=self.cols, sun=self.sun)
        self.lawnmowers = [True] * self.lanes
        return self._get_obs()

    def step(self, action):
        """Perform an action in the environment"""
        if action < self.num_plants * self.lanes * (self.cols - 2):
            # Decode the action into plant, lane, and column
            plant_index = action // (self.lanes * (self.cols - 2))
            remaining_action = action % (self.lanes * (self.cols - 2))
            lane = remaining_action // (self.cols - 2)
            col = remaining_action % (self.cols - 2) + 2  # Offset by 2 for home and lawnmower columns

            plant = self.plants[plant_index]
            success = buy_and_place(self.game, lane=lane, col=col, plant=plant)
        else:
            # Action to skip planting and advance time
            success = True

        # Always advance time by 1 second after an action
        self.game.advance_time(1)

        # Move zombies, generate sun, spawn new zombies, etc.
        move_zombies(self.game)
        update_sun_production(self.game)
        if self.game.get_game_time() > 18 and np.random.rand() < 0.2:  # 20% chance to spawn a zombie
            zombie = self._weighted_random_zombie_choice(self.zombies)
            lane = np.random.randint(0, self.lanes)
            if self._can_spawn_zombie_in_lane(lane):
                spawn_zombie(self.game, name=zombie.name, hp=zombie.hp, dmg=zombie.dmg, walk_speed=zombie.walk_speed,
                             extra_health=zombie.extra_health)

        # Calculate reward
        reward = self._calculate_reward()
        done = self._is_done()

        return self._get_obs(), reward, done, {}

    def render(self, mode='human'):
        """Render the game state"""
        print_field(self.game)

    def _get_obs(self):
        """Return the current state as a flattened array"""
        field = self.game.field.flatten()
        return np.append(field, self.game.sun)

    def _calculate_reward(self):
        """Calculate the reward based on the current state"""
        reward = 1  # Reward for surviving a time step

        # Check for immediate game-ending conditions
        for lane in range(self.lanes):
            if isinstance(self.game.field_objects[lane][0], Zombie):  # Zombie reached home column
                reward -= 1000  # Large penalty for losing the game
                return reward
            elif isinstance(self.game.field_objects[lane][1], Zombie) and not self.lawnmowers[
                lane]:  # Zombie reached lawnmower column and no lawnmower
                reward -= 500  # Significant penalty for losing the lawnmower defense
                return reward

        return reward

    def _is_done(self):
        """Check if the game is over"""
        for lane in range(self.lanes):
            if isinstance(self.game.field_objects[lane][0], Zombie):  # Game over if zombie reaches home
                return True
            elif isinstance(self.game.field_objects[lane][1], Zombie) and not self.lawnmowers[
                lane]:  # Game over if zombie reaches lawnmower column with no defense
                return True
        return False

    def _can_spawn_zombie_in_lane(self, lane):
        """Check if there are fewer than 4 zombies in the last column of the given lane"""
        zombie_count = sum(isinstance(obj, Zombie) for obj in self.game.field_objects[lane])
        return zombie_count < 4

    def _weighted_random_zombie_choice(self, zombies):
        """Select a zombie weighted by their health, favoring those with lower health"""
        total_health = sum(z.hp for z in zombies.values())
        if total_health == 0:
            # Handle the edge case where all zombies have zero health, which shouldn't typically happen
            weights = [1.0 / len(zombies)] * len(zombies)
        else:
            weights = [(total_health - z.hp) for z in zombies.values()]

        # Normalize weights to sum to 1
        total_weight = sum(weights)

        if total_weight > 0:
            normalized_weights = [w / total_weight for w in weights]
        else:
            # Fallback: if weights don't sum to more than 0, return equal probabilities
            normalized_weights = [1.0 / len(zombies)] * len(zombies)

        # Ensure the probabilities sum to 1 due to floating-point precision
        normalized_weights = np.array(normalized_weights)
        normalized_weights /= normalized_weights.sum()

        return np.random.choice(list(zombies.values()), p=normalized_weights)
