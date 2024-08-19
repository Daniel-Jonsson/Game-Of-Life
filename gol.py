#!/usr/bin/env python
"""
The universe of the Game of Life is an infinite two-dimensional orthogonal grid of square cells,
each of which is in one of two possible states, alive or dead (populated or unpopulated).
Every cell interacts with its eight neighbours, which are the cells that are horizontally,
vertically, or diagonally adjacent.

At each step in time, the following transitions occur:

****************************************************************************************************
   1. Any live cell with fewer than two live neighbours dies, as if caused by underpopulation.
   2. Any live cell with two or three live neighbours lives on to the next generation.
   3. Any live cell with more than three live neighbours dies, as if by overpopulation.
   4. Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
****************************************************************************************************

The initial pattern constitutes the seed of the system.

The first generation is created by applying the above rules simultaneously to every cell in the
seed—births and deaths occur simultaneously, and the discrete moment at which this happens is
sometimes called a tick. The rules continue to be applied repeatedly to create further generations.

You run this script as a module:
    python -m Project.gol.py
"""

import argparse
import ast
import json
import logging
import itertools
import random
from pathlib import Path
from time import sleep

import Project.code_base as cb

__version__ = '1.0'
__desc__ = "A simplified implementation of Conway's Game of Life."

RESOURCES = Path(__file__).parent / "../_Resources/"


# -----------------------------------------
# IMPLEMENTATIONS FOR HIGHER GRADES, C - B
# -----------------------------------------


def load_seed_from_file(_file_name: str) -> tuple:
    """ Load population seed from file. Returns tuple: population (dict) and world_size (tuple). """
    population = {}  # Populate dict
    world_size = ()
    if ".json" not in _file_name:
        _file_name = _file_name + ".json"
    _file_name = RESOURCES / _file_name  # Gets the seed from _Resources
    with open(_file_name, 'r', encoding='utf-8') as pat_world:
        loaded = json.load(pat_world)  # Parse and save the file to a dict variable.
        # Go through all items in dict, in this case world size and population
        for key, val in loaded.items():
            if key in 'world_size':
                world_size = tuple(val)
            else:
                # Here the string from key is removed with ast.literal_eval.
                population = {ast.literal_eval(key): value for key, value in val.items()}
        # This is changing coordinate from y,x to x,y in every key.
        population = {key[::-1]: value for key, value in population.items()}
        for value in population.values():
            if value is not None:
                # Make a list of tuples instead of nested list and change from y,x to x,y on every coord.
                value['neighbours'] = [tuple(neighbour[::-1]) for neighbour in value['neighbours']]
        return population, world_size


def create_logger() -> logging.Logger:
    """ Creates a logging object to be used for reports. """
    default_path = RESOURCES / "gol.log"  # Sets path for logging
    logger = logging.getLogger('gol_logger')
    logger.setLevel(20)  # Sets logging level to INFO, you can do this with values also.
    file_handler = logging.FileHandler(default_path, 'w')
    logger.addHandler(file_handler)  # Adds a file handler, so program know where to store it.
    return logger


def simulation_decorator(func):
    """ Function decorator, used to run full extent of simulation. """
    def wrapper(nth_gen: int, _population_: dict, world_size: tuple):
        logger = create_logger()    # Gets the logger
        alive, alive_elders, alive_primes, dead, rim = [0]*5
        for i in range(nth_gen):
            cb.clear_console()  # Removes last generation
            for k in _population_.values():  # Used to check all cells state
                if k is None:
                    rim += 1
                    continue
                # If the cell is alive count up the alive variable.
                if k['state'] == cb.STATE_ALIVE:
                    alive += 1
                elif k['state'] == cb.STATE_ELDER:
                    alive_elders += 1
                    alive += 1
                elif k['state'] == cb.STATE_PRIME_ELDER:
                    alive_primes += 1
                    alive += 1
                else:
                    dead += 1
                    # Gets the information to log
            formatting = [f'GENERATION {i}', f'Population: {len(_population_)-rim}', f'Alive: {alive}',
                          f'Elders: {alive_elders}', f'Prime Elders: {alive_primes}', f'Dead: {dead}']
            for count, item in enumerate(formatting):
                logger.info("%s", item) if count == 0 else logger.info("%s", item.rjust(len(item)+2))
            alive, alive_elders, alive_primes, dead, rim = [0]*5
            # Assign what's returned from function to _population_
            # We know func returns the updated world as seen in run_simulation
            _population_ = func(nth_gen, _population_, world_size)
            sleep(.2)
    return wrapper


# -----------------------------------------
# BASE IMPLEMENTATIONS
# -----------------------------------------

def parse_world_size_arg(_arg: str) -> tuple:
    """ Parse width and height from command argument. """
    try:
        # If the argument can be cast to int and not empty add to variable
        arguments = tuple(int(x) for x in _arg.split('x') if x != "" and _arg.count('x') <= 1)
        assert len(arguments) == 2, \
            "World size should contain width and height, separated by 'x'. Ex: '80x40'"
        for argument in arguments:  # Checks every element in tuple
            if argument < 1:
                raise ValueError("Both width and height needs to have positive values above zero.")
        return arguments
    except (AssertionError, ValueError) as error:
        print(f"{error}\nUsing default world size: 80x40")
        return 80, 40


def get_dead_world(_world_size: tuple) -> dict:
    """ Creates a world with only rims and dead cells. """
    world = {}
    # Gets all cells inside world size
    cells_in_world = [(x, y) for y, x in itertools.product(range(_world_size[1]), range(_world_size[0]))]
    # Gets the end of width and height with list comprehension, '_' is a dummy variable.
    end_width, end_height = [_-1 for _ in _world_size]
    for cell in cells_in_world:
        if cell[0] == end_width or cell[1] == end_height or 0 in cell:
            world[cell] = None
        else:
            world[cell] = {'state': cb.STATE_DEAD}
    return world


def get_random_world(_world_: dict) -> dict:
    """ Gets a random generated world with help of random.randint() """
    world = _world_
    for cell, value in world.items():
        neighbours = calc_neighbour_positions(cell)
        # If cell is not a rim cell and randint is higher than 16, it's alive.
        if value is not None and random.randint(0, 20) > 16:
            world[cell] = {'state': cb.STATE_ALIVE, 'neighbours': neighbours, 'age': 1}
        elif value is not None:
            world[cell] = {'state': cb.STATE_DEAD, 'neighbours': neighbours, 'age': 0}
    return world


def populate_world(_world_size: tuple, _seed_pattern: str = None) -> dict:
    """ Populate the world with cells and initial states. """
    population = {}
    world = get_dead_world(_world_size) # Get all possible cells
    get_pattern = cb.get_pattern(_seed_pattern, _world_size)
    # Changed the pattern from y,x to x,y with the help of list comprehension and slicing.
    # If the variable get_pattern is not None, if it is None the variable is set to get_pattern.
    pattern = [x[::-1] for x in get_pattern] if get_pattern is not None else get_pattern
    for cell, state in world.items():
        if pattern is not None:
            if state is not None and cell in pattern:
                neighbours = calc_neighbour_positions(cell)
                population[cell] = {'state': cb.STATE_ALIVE, 'neighbours': neighbours, 'age': 1}
            elif state is not None:
                neighbours = calc_neighbour_positions(cell)
                population[cell] = {'state': cb.STATE_DEAD, 'neighbours': neighbours, 'age': 0}
            else:
                population[cell] = None
    if pattern is None:
        population = get_random_world(world)
    return population


def calc_neighbour_positions(_cell_coord: tuple) -> list:
    """ Calculate neighbouring cell coordinates in all directions (cardinal + diagonal).
    Returns list of tuples. """
    x, y = _cell_coord
    offset = (-1, 0, 1)
    neighbour_list = []
    # Gets all the neighbouring cells with help of itertools.product
    for x_offset, y_offset in itertools.product(offset, repeat=2):
        if (x + x_offset, y + y_offset) == (x, y):
            continue
        neighbour_list.append((x + x_offset, y + y_offset))
    return neighbour_list


@simulation_decorator
def run_simulation(nth_generation: int, _population: dict, _world_size: tuple):
    """ Runs simulation for specified amount of generations. """
    return update_world(_population, _world_size)


def is_elder(world: dict, cell: tuple) -> dict:
    """ Determines if cell should turn into elder """
    if world[cell]['age'] > 5:
        world[cell]['state'] = cb.STATE_ELDER
    return world[cell]


def is_prime(world: dict, cell: tuple) -> dict:
    """ Determines if cell should turn into prime elder. """
    if world[cell]['age'] > 10:
        world[cell]['state'] = cb.STATE_PRIME_ELDER
    return world[cell]


def get_updated_world(_cur_gen: dict, _world_size: tuple) -> dict:
    """ Gets the updated world, later used in update_world() """
    new_world = {}
    alive, dead, elder, prime = cb.STATE_ALIVE, cb.STATE_DEAD, cb.STATE_ELDER, cb.STATE_PRIME_ELDER
    for cell, values in _cur_gen.items():
        if values is not None:
            if 'age' not in values:
                values['age'] = 1 if values['state'] == cb.STATE_ALIVE else 0
            ages = values['age']
            neighbours = values['neighbours']
            alive_neighbours = count_alive_neighbours(neighbours, _cur_gen)
            if values['state'] in (alive, elder, prime) and alive_neighbours in (2, 3):  # Cell aging.
                new_world[cell] = {'state': values['state'], 'neighbours': neighbours, 'age': ages + 1}
                is_elder(new_world, cell), is_prime(new_world, cell)  # Changes cell state depending on cell age.
            elif values['state'] == dead and alive_neighbours == 3:
                new_world[cell] = {'state': alive, 'neighbours': neighbours, 'age': 1}  # Reproduction.
            else:
                new_world[cell] = {'state': dead, 'neighbours': neighbours, 'age': 0}   # Dying/dead cell.
        else:
            new_world[cell] = None  # Rim cell
    return new_world


def update_world(_cur_gen: dict, _world_size: tuple) -> dict:
    """ Represents a tick in the simulation. """
    print_val = ""
    for cell, value in _cur_gen.items():
        if value is not None:
            print_val += cb.get_print_value(value['state'])  # alive/dead cell state 'X','-'
        elif cell[0] == _world_size[0] - 1:
            print_val += f"{cb.get_print_value(cb.STATE_RIM)}\n"  # Rim cell at end of width needs new line.
        else:
            print_val += cb.get_print_value(cb.STATE_RIM)   # Rim cell.
    cb.progress(print_val)
    return get_updated_world(_cur_gen, _world_size)  # Gets the updated world.


def count_alive_neighbours(_neighbours: list, _cells: dict) -> int:
    """ Determine how many of the neighbouring cells are currently alive. """
    alive = 0
    for neighbour in _neighbours:
        if _cells[neighbour] is None:   # If the neighbour is a rim cell, ignore it.
            continue
        # If its alive we add 1 to alive variable.
        if _cells[neighbour]['state'] in (cb.STATE_ALIVE, cb.STATE_ELDER, cb.STATE_PRIME_ELDER):
            alive += 1
    return alive


def main():
    """ The main program execution. YOU MAY NOT MODIFY ANYTHING IN THIS FUNCTION!! """
    epilog = "DT179G Project v" + __version__
    parser = argparse.ArgumentParser(description=__desc__, epilog=epilog, add_help=True)
    parser.add_argument('-g', '--generations', dest='generations', type=int, default=50,
                        help='Amount of generations the simulation should run. Defaults to 50.')
    parser.add_argument('-s', '--seed', dest='seed', type=str,
                        help='Starting seed. If omitted, a randomized seed will be used.')
    parser.add_argument('-ws', '--worldsize', dest='worldsize', type=str, default='80x40',
                        help='Size of the world, in terms of width and height. Defaults to 80x40.')
    parser.add_argument('-f', '--file', dest='file', type=str,
                        help='Load starting seed from file.')

    args = parser.parse_args()

    try:
        if not args.file:
            raise AssertionError
        population, world_size = load_seed_from_file(args.file)
    except (AssertionError, FileNotFoundError):
        world_size = parse_world_size_arg(args.worldsize)
        population = populate_world(world_size, args.seed)

    run_simulation(args.generations, population, world_size)


if __name__ == "__main__":
    main()
