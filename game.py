import random
from logic import Game, Plant, Zombie, buy_and_place, print_field, update_sun_production, move_zombies, spawn_zombie
from dbops import create_connection, get_all_plants, get_all_zombies, close_connection


class GameOverException(Exception):
    pass


def _weighted_random_zombie_choice(self, zombies):
    """Select a zombie weighted by their health, favoring those with lower health."""
    total_health = sum(z.hp for z in zombies.values())
    if total_health == 0:
        # Handle the edge case where all zombies have zero health, which shouldn't typically happen
        weights = [1.0 / len(zombies)] * len(zombies)
    else:
        weights = [(total_health - z.hp) / total_health for z in zombies.values()]

    # Normalize weights to sum to 1
    total_weight = sum(weights)
    if total_weight > 0:
        normalized_weights = [w / total_weight for w in weights]
    else:
        normalized_weights = [1.0 / len(zombies)] * len(zombies)

    return np.random.choice(list(zombies.values()), p=normalized_weights)


def spawn_random_sun(game):
    """ Simulate random sun falling and being collected by the player. """
    sun_drop = 25
    game.sun += sun_drop
    print(f"Random sun dropped and collected! Current sun: {game.sun}")


def activate_lawnmower(game, lane, lawnmowers):
    """ Activate the lawnmower, which destroys all zombies in the lane. """
    print(f"Lawnmower activated in lane {lane + 1}!")
    for col in range(2, game.cols):  # Clear all zombies from col2 onwards
        if isinstance(game.field_objects[lane][col], Zombie):
            print(f"Zombie in column {col + 1} of lane {lane + 1} was run over by the lawnmower.")
            game.field_objects[lane][col] = None
    lawnmowers[lane] = False  # Mark the lawnmower as activated


def can_spawn_zombie_in_lane(game, lane):
    """ Check if there are fewer than 4 zombies in the last column of the given lane. """
    zombie_count = sum(isinstance(obj, Zombie) for obj in game.field_objects[lane])
    return zombie_count < 4


def prompt_for_plant_placement(plants):
    """ Prompt the user to place plants and return the chosen plant, lane, and column. """
    print("\nAvailable plants:")
    for i, plant_name in enumerate(plants.keys()):
        print(f"{i + 1}. {plant_name}")
    print(f"{len(plants) + 1}. Skip planting and advance time")

    plant_choice = int(input("Select a plant by number: ")) - 1

    if plant_choice == len(plants):
        return None, None, None  # Indicate that the player chose to skip planting

    plant_name = list(plants.keys())[plant_choice]

    lane = int(input(f"Enter lane (1-{lanes}): ")) - 1
    col = int(input(f"Enter column (3-{cols}): ")) - 1  # Columns start from 2 due to home and lawnmower columns

    return plant_name, lane, col


def main():
    # Create a connection to the database
    conn = create_connection()

    if conn is None:
        print("Failed to connect to the database. Exiting...")
        return

    # Fetch all plants and zombies from the database
    plants_data = get_all_plants(conn)
    zombies_data = get_all_zombies(conn)

    # Create a dictionary to store Plant and Zombie objects by name
    plants = {}
    zombies = {}

    for plant_data in plants_data:
        plant_id, name, hp, dmg, dps, fire_rate, cost, cd = plant_data
        sun_production = 25 if name == 'Sunflower' else 0
        plants[name] = Plant(name=name, hp=hp, dmg=dmg, dps=dps, fire_rate=fire_rate, cost=cost, cd=cd,
                             sun_production=sun_production)

    for zombie_data in zombies_data:
        zombie_id, name, hp, dmg, walk_speed, extra_health, *rest = zombie_data
        zombies[name] = Zombie(name=name, hp=hp, dmg=dmg, walk_speed=walk_speed, extra_health=extra_health, lane=0,
                               start_col=10)

    # Close the database connection
    close_connection(conn)

    # Game setup
    global lanes, cols  # Making these global for the input function
    lanes = 5
    cols = 11  # Extend the game field to include home (col0) and lawnmowers (col1)
    sun = 150  # Starting sun points
    game = Game(world=1, lanes=lanes, cols=cols, sun=sun)
    lawnmowers = [True] * lanes  # Lawn mowers are initially available for all lanes

    # Display initial field
    print("Initial Game Field:")
    print_field(game)

    # Main game loop
    total_simulation_time = 60  # Total simulation time in seconds
    elapsed_time = 0

    next_sun_drop_time = random.randint(8, 12)  # Schedule the first random sun drop

    try:
        while elapsed_time < total_simulation_time:
            # Ask the user if they want to place a plant
            while True:
                plant_name, lane, col = prompt_for_plant_placement(plants)
                if plant_name is None:
                    break  # Player chose to skip planting

                success = buy_and_place(game, lane=lane, col=col, plant=plants[plant_name])
                print_field(game)

                if success:
                    break  # Exit the loop if the plant was successfully placed

            # Advance time by 1 second
            game.advance_time(1)

            # Random sun drop
            if elapsed_time >= next_sun_drop_time:
                spawn_random_sun(game)
                next_sun_drop_time += random.randint(8, 12)  # Schedule the next sun drop

            # Spawn zombies only after 18 seconds have passed
            if game.get_game_time() > 18:
                if random.randint(1, 10) > 8:  # 20% chance to spawn a zombie each second
                    # Choose a zombie weighted by lower health
                    zombie = weighted_random_zombie_choice(zombies)
                    lane = random.randint(0, game.lanes - 1)
                    if can_spawn_zombie_in_lane(game, lane):
                        spawn_zombie(game, name=zombie.name, hp=zombie.hp, dmg=zombie.dmg,
                                     walk_speed=zombie.walk_speed, extra_health=zombie.extra_health)
                    else:
                        print(f"Lane {lane + 1} is full and cannot spawn more zombies.")

            # Move zombies
            move_zombies(game)

            # Generate sun from Sunflower and update the game state
            update_sun_production(game)

            # Check for lawnmower activation or game over
            for lane in range(game.lanes):
                if isinstance(game.field_objects[lane][1], Zombie):  # Check if a zombie is in col1
                    if lawnmowers[lane]:
                        activate_lawnmower(game, lane, lawnmowers)
                        game.field_objects[lane][1] = None  # Remove the zombie in col1 after lawnmower activation
                    else:
                        raise GameOverException(
                            f"Game Over! A zombie reached the lawnmower column (col1) in lane {lane + 1} and no lawnmower is available.")

                elif isinstance(game.field_objects[lane][0], Zombie):  # Check if a zombie is in col0 (home)
                    raise GameOverException(f"Game Over! A zombie reached the home column in lane {lane + 1}.")

            # Print game status every second
            print(f"Time: {game.get_game_time()} seconds")
            print(f"Current sun: {game.sun}")
            print_field(game)
            elapsed_time += 1

    except GameOverException as e:
        print(e)

    # Final display of the game field and sun points
    print("Final Game Field:")
    print_field(game)
    print(f"Final sun points: {game.sun}")


if __name__ == "__main__":
    main()
