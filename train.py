import numpy as np
from agent import DQNAgent
from environment import PvZEnv
from dbops import create_connection, get_all_plants, get_all_zombies, close_connection
from logic import *

def main():
    # Load plants and zombies data from the database
    conn = create_connection()
    plants_data = get_all_plants(conn)
    zombies_data = get_all_zombies(conn)
    close_connection(conn)

    # Create a dictionary to store Plant and Zombie objects by name
    plants = {}
    zombies = {}

    for plant_data in plants_data:
        plant_id, name, hp, dmg, dps, fire_rate, cost, cd = plant_data
        sun_production = 25 if name == 'Sunflower' else 0
        plants[name] = Plant(name=name, hp=hp, dmg=dmg, dps=dps, fire_rate=fire_rate, cost=cost, cd=cd, sun_production=sun_production)

    for zombie_data in zombies_data:
        zombie_id, name, hp, dmg, walk_speed, extra_health, *rest = zombie_data
        zombies[name] = Zombie(name=name, hp=hp, dmg=dmg, walk_speed=walk_speed, extra_health=extra_health, lane=0, start_col=10)

    # Initialize the environment and the agent
    env = PvZEnv(plants, zombies)
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    agent = DQNAgent(state_size, action_size)
    episodes = 1000  # Number of episodes to train the agent
    batch_size = 32  # Batch size for experience replay

    # Main training loop
    for e in range(episodes):
        state = env.reset()  # Reset the environment for a new episode
        state = np.reshape(state, [1, state_size])  # Reshape the state for the model input

        for time in range(500):  # Maximum number of time steps per episode
            env.render()  # Optional: render the environment (print the game field)
            action = agent.act(state)  # Choose an action based on the current state
            next_state, reward, done, _ = env.step(action)  # Take the action in the environment
            reward = reward if not done else -1000  # Apply a large penalty for losing
            next_state = np.reshape(next_state, [1, state_size])  # Reshape the next state for the model input
            agent.remember(state, action, reward, next_state, done)  # Store the experience in memory
            state = next_state  # Move to the next state

            if done:
                print(f"episode: {e}/{episodes}, score: {time}, e: {agent.epsilon:.2f}")
                break  # End the episode if the game is over

            if len(agent.memory) > batch_size:
                agent.replay(batch_size)  # Train the agent using experience replay

        if e % 50 == 0:  # Save the model every 50 episodes
            agent.save(f"models/dqn_model_episode_{e}.h5")

if __name__ == "__main__":
    main()
