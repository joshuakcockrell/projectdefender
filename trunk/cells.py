##### RANDOM MAP GENERATOR #####
import pygame
import random
import math
import time


class MapGrid():
    def __init__(self, map_width, map_height, number_of_generations):

        self.number_of_rooms = number_of_rooms
        self.map_width = map_width
        self.map_height = map_width

        # generate outside rooms
        self.empty_outside_terrain_grid = self._generate_empty_noise_grid(self.map_width, self.map_height)
        self.outside_terrain_grid = self._generate_outside_terrain(self.empty_outside_terrain_grid, number_of_generations)

    def _generate_empty_map_grid(self, map_width, map_height):
        '''
        creates a new 2d array with the given specs
        '''

        new_map_grid = [] # create our new list
        for x in range(map_width):
            new_map_grid.append([]) # add our columns to the array
            for y in range(map_height):
                new_map_grid[x].append(0) # fill in our rows

        return new_map_grid

    def _generate_empty_noise_grid(self, map_width, map_height):
        '''
        creates a new 2d array with the given specs
        and filled with random 1s and 0s
        '''

        new_map_grid = [] # create our new list
        for x in range(map_width):
            new_map_grid.append([]) # add our columns to the array
            for y in range(map_height):
                new_map_grid[x].append(random.choice([0,1])) # fill in our rows

        return new_map_grid



    def _generate_outside_terrain(self, empty_outside_terrain_grid, number_of_generations):
        '''
        creates a bubble effect with cellular automaton
        '''
        grid = empty_outside_terrain_grid
        number_of_generations = number_of_generations

        for x in range(number_of_generations):
            next_grid = []
            for column_index, column in enumerate(grid):
                next_column = []
                next_grid.append(next_column)
                for tile_index, tile in enumerate(column):
                    
                    top_left = grid[column_index - 1][tile_index - 1]
                    top_mid = grid[column_index][tile_index - 1]
                    try:
                        top_right = grid[column_index + 1][tile_index - 1]
                    except IndexError:
                        top_right = 0
                    
                    center_left = grid[column_index - 1][tile_index]
                    center_mid = grid[column_index][tile_index]
                    try:
                        center_right = grid[column_index + 1][tile_index]
                    except IndexError:
                        center_right = 0

                    try:
                        bottom_left = grid[column_index - 1][tile_index + 1]
                    except IndexError:
                        bottom_left = 0
                    try:
                        bottom_mid = grid[column_index][tile_index + 1]
                    except IndexError:
                        bottom_mid = 0
                    try:
                        bottom_right = grid[column_index + 1][tile_index + 1]
                    except IndexError:
                        bottom_right = 0

                    close_neighbors = (top_mid + center_left + center_mid +
                                       center_right + bottom_mid)

                    far_neighbors = (top_left + top_right +
                                     bottom_left + bottom_right)

                    number_of_neighbors = close_neighbors + far_neighbors

                    if number_of_neighbors > random.choice([3,4,5]):
                        next_cell = 1

                    else:
                        next_cell = 0

                    if close_neighbors > 3:
                        next_cell = 1

                    next_column.append(next_cell)
            grid = next_grid

                    
                    
                    
        return next_grid



                    
if __name__ == '__main__':
    # general map stats
    map_width = 200
    map_height = 200
    number_of_rooms = 1
    starting_room_direction = 'center'

    # random rooms stats
    max_room_width = 5
    max_room_height = 5
    min_room_width = 3
    min_room_height = 3
    max_hall_length = 5
    min_hall_length = 3
    room_size_multiplier = 1.2
    number_of_generations = 1
    tile_size = 4
    
    map_grid = MapGrid(map_width, map_height, number_of_generations)
    #print map_grid.outside_terrain_grid

    pygame.init()

    screen = pygame.display.set_mode((map_width * tile_size,map_height * tile_size))

    one_tile = pygame.Surface((1, 1))
    one_tile.fill((0,0,0))
    zero_tile = pygame.Surface((1, 1))
    zero_tile.fill((255,255,255))
    colors = {0: zero_tile, 1: one_tile}

    background = pygame.Surface((map_width * tile_size,map_height * tile_size))

    clock = pygame.time.Clock()

    first_gen = True
    
    running = True
    while running == True:
        clock.tick(3)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if first_gen:
            themap = map_grid.outside_terrain_grid
        else:
            themap = map_grid._generate_outside_terrain(themap, 1)

        for column_index, column in enumerate(themap):
            for tile_index, tile in enumerate(column):
                screen.blit(colors[tile], (tile_index * tile_size, column_index * tile_size))

        pygame.display.flip()

        if first_gen:
            time.sleep(4)
            first_gen = False

    pygame.quit()
            
    
