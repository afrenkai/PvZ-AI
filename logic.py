import numpy as np
import random
from constants import *


# Game class to manage the game state
class Game:
    def __init__(self, world: int, lanes: int, cols: int, sun: int):
        self.world = world
        self.lanes = lanes
        self.cols = cols
        self.field = np.zeros(shape=(lanes, cols), dtype=np.int8)
        self.field_objects = [[None for _ in range(cols)] for _ in range(lanes)]  # Track Plant and Zombie objects
        self.sun = sun
        self.game_time = 0  # Initialize game time to 0

    def advance_time(self, seconds: int = 1):
        self.game_time += seconds

    def get_game_time(self) -> int:
        return self.game_time

    def get_cd(self, plant: 'Plant') -> float:
        time_passed = self.get_game_time()
        if time_passed <= 18:
            if plant.cd == FAST:
                return INITIAL_FAST
            elif plant.cd == SLOW:
                return INITIAL_SLOW
            elif plant.cd == VERY_SLOW:
                return INITIAL_VERY_SLOW
        return plant.cd


# Plant class to define plant attributes and behavior
class Plant:
    def __init__(self, name: str, hp: int, dmg: int, dps: float, fire_rate: float, cost: int, cd: float, sun_production: int = 0):
        self.name = name
        self.hp = hp
        self.dmg = dmg
        self.dps = dps
        self.fire_rate = fire_rate  # Time in seconds between sun generation
        self.cost = cost
        self.cd = cd
        self.sun_production = sun_production  # Amount of sun generated after cooldown
        self.last_generated_time = None  # Track the last time sun was generated
        self.last_planted = -float('inf')  # Track the last time this plant was placed
        self.first_sun_delay = random.randint(20, 24)  # Initial delay for the first sun generation

    def generate_sun(self, current_time):
        if self.sun_production > 0:
            if self.last_generated_time is None:
                # Handle the first sun generation with the initial delay
                if (current_time - self.last_planted) >= self.first_sun_delay:
                    self.last_generated_time = current_time
                    return self.sun_production, current_time
            elif (current_time - self.last_generated_time) >= self.fire_rate:
                # Subsequent sun generation after the initial one
                self.last_generated_time = current_time
                return self.sun_production, current_time
        return 0, None


# Zombie class to define zombie attributes and behavior
class Zombie:
    def __init__(self, name: str, hp: int, dmg: int, walk_speed: float, extra_health: int, lane: int, start_col: int):
        self.name = name
        self.hp = hp
        self.dmg = dmg
        self.walk_speed = walk_speed  # Time it takes to move one cell
        self.extra_health = extra_health  # Extra health soaked up by the corpse
        self.lane = lane
        self.position = start_col  # Start at the rightmost column
        self.last_moved_time = 0  # Track the last time the zombie moved

    def advance(self, game_time: int):
        if game_time - self.last_moved_time >= self.walk_speed:
            self.position -= 1  # Move one cell to the left
            self.last_moved_time = game_time
            return True  # Zombie has moved
        return False  # Zombie hasn't moved yet

    def take_damage(self, damage: int):
        if self.hp > 0:
            self.hp -= damage
            if self.hp <= 0:
                print(f"{self.name} in lane {self.lane + 1} has been killed. Its corpse will soak up {self.extra_health} more damage.")
        else:
            self.extra_health -= damage
            if self.extra_health <= 0:
                print(f"The corpse of {self.name} in lane {self.lane + 1} has been fully destroyed.")
                return True  # The zombie is completely destroyed
        return False  # The zombie or its corpse is still soaking up damage


# Function to update sun production across all plants
def update_sun_production(game: Game):
    total_sun_generated = 0
    current_time = game.get_game_time()
    for lane in range(game.lanes):
        for col in range(game.cols):
            plant = game.field_objects[lane][col]
            if isinstance(plant, Plant) and plant.sun_production > 0:
                sun_generated, generation_time = plant.generate_sun(current_time)
                total_sun_generated += sun_generated
                if sun_generated > 0:
                    print(f"{plant.name} generated {sun_generated} sun at time {generation_time} seconds at lane {lane + 1}, column {col + 1}.")

    game.sun += total_sun_generated
    print(f"Total sun generated this round: {total_sun_generated}. Current sun: {game.sun}.")


# Function to check if the player can afford a plant
def afford_check(sun: int, plant: Plant):
    return sun >= plant.cost


# Function to place a plant on the field
def place_plant(game: Game, lane: int, col: int, plant: Plant) -> bool:
    current_time = game.get_game_time()
    cooldown = game.get_cd(plant)

    if current_time - plant.last_planted < cooldown:
        print(f"{plant.name} is still on cooldown. Please wait {cooldown - (current_time - plant.last_planted):.2f} seconds.")
        return False

    if game.field[lane, col] == 0:  # If the spot is empty
        game.field[lane, col] = 1  # Mark the field with a plant
        game.field_objects[lane][col] = plant  # Track the plant object
        plant.last_planted = current_time
        print(f'Placed {plant.name} at lane {lane + 1}, column {col + 1}.')
        return True
    else:
        print("That spot already has a plant in it.")
        return False


# Function to buy and place a plant
def buy_and_place(game: Game, lane: int, col: int, plant: Plant):
    if afford_check(game.sun, plant):
        if place_plant(game, lane, col, plant):
            game.sun -= plant.cost
            print(f'Remaining Sun: {game.sun}')
        else:
            print('Failed to place plant.')
    else:
        print('Not enough sun to buy the plant.')


# Function to spawn a zombie in a random lane
def spawn_zombie(game: Game, name: str, hp: int, dmg: int, walk_speed: float, extra_health: int):
    lane = random.randint(0, game.lanes - 1)
    zombie = Zombie(name, hp, dmg, walk_speed, extra_health, lane, game.cols - 1)
    game.field_objects[lane][game.cols - 1] = zombie
    print(f"{name} spawned in lane {lane + 1} at column {game.cols}.")


# Function to move zombies across the field
def move_zombies(game: Game):
    current_time = game.get_game_time()
    for lane in range(game.lanes):
        for col in reversed(range(game.cols)):  # Start from the rightmost cell
            zombie = game.field_objects[lane][col]
            if isinstance(zombie, Zombie):
                if zombie.advance(current_time):
                    new_col = zombie.position
                    if new_col >= 0:
                        game.field_objects[lane][new_col] = zombie  # Move zombie to new position
                        game.field_objects[lane][col] = None  # Clear old position
                        print(f"{zombie.name} moved to column {new_col + 1} in lane {lane + 1}.")
                    else:
                        print(f"{zombie.name} has reached the end of lane {lane + 1} and is attacking the house!")
                        game.field_objects[lane][col] = None  # Remove the zombie from the field


# Function to print the current game field
def print_field(game: Game):
    field_visual = ""
    for lane in range(game.lanes):
        for col in range(game.cols):
            obj = game.field_objects[lane][col]
            if obj is None:
                field_visual += "[ ]"  # Empty space
            elif isinstance(obj, Plant):
                field_visual += f"[{obj.name[:4]}]"  # First four letters of the plant's name
            elif isinstance(obj, Zombie):
                field_visual += f"[{obj.name[:4]}]"  # First four letters of the zombie's name
        field_visual += "\n"  # New line after each lane
    print(field_visual)
