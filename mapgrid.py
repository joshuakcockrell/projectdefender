##### RANDOM MAP GENERATOR #####

import random

class MapGrid():
    def __init__(self, map_width, map_height, number_of_rooms,
                 max_room_width, max_room_height,
                 mini_room_width, min_room_height):

        self.number_of_rooms = number_of_rooms
        self.map_width = map_width
        self.map_height = map_width

        # create a grid which holds the terrain image information
        self.empty_terrain_map_grid = self._generate_new_empty_map_grid(self.map_width, self.map_height)
        #self.terrain_map_grid = self._generate_terrain_map_random_walk(self.empty_terrain_map_grid)

        self.terrain_map_grid = self._generate_terrain_map_random_rooms(self.empty_terrain_map_grid,
                                           max_room_width, max_room_height,
                                           min_room_width, min_room_height)
        # create a grid which holds the collision tile information
        self.empty_collision_map_grid = self._generate_new_empty_map_grid(self.map_width, self.map_height)

        # create a grid which holds the gravitational tile information
        self.empty_gravity_map_grid = self._generate_new_empty_map_grid(self.map_width, self.map_height)

        # create a grid which holds the flood fill AI influence map
        self.empty_influence_map_grid = self._generate_new_empty_map_grid(self.map_width, self.map_height)

    def _generate_new_empty_map_grid(self, map_width, map_height):
        '''
        creates a new 2d array with the given specs
        '''

        new_map_grid = [] # create our new list
        for w in range(map_width):
            new_map_grid.append([]) # add our columns to the array
            for h in range(map_height):
                new_map_grid[w].append(0) # fill in our rows

        return new_map_grid

    def _get_random_direction(self):
        '''
        generates a random direction,
        used in the random walk algorithm
        '''
        random_direction = random.choice(['right', 'up', 'left', 'down'])

        return random_direction

    def _generate_terrain_map_random_walk(self, empty_terrain_map_grid):
        '''
        fills up our terrain grid with rooms.
        '''
        terrain_map_grid = empty_terrain_map_grid
        
        current_position_x = self.map_width / 2
        current_position_y = self.map_height / 2
        current_room_number = 0
        while current_room_number < self.number_of_rooms:
            current_room_number += 1

            # move to a new spot to create a room
            direction = self._get_random_direction()
            if direction == 'right':
                # check for out of bounds
                if current_position_x < map_width:
                    current_position_x += 1
            if direction == 'up':
                if current_position_y > 0:
                    current_position_y -= 1
            if direction == 'left':
                if current_position_x > 0:
                    current_position_x -= 1
            if direction == 'down':
                if current_position_y < map_height:
                    current_position_y += 1
            
            # create a room
            terrain_map_grid[current_position_x - 1][current_position_y - 1] += 1

        return terrain_map_grid

    def _generate_terrain_map_random_rooms(self, empty_terrain_map_grid,
                                           max_room_width, max_room_height,
                                           min_room_width, min_room_height):
        '''
        fills up or grid with more clearly defined rooms
        room variables:
        0 = empty
        1 = floor
        2 = closed wall (unable to build off of)
        3 = right wall
        4 = up wall
        5 = left wall
        6 = down wall
        '''

        terrain_map_grid = empty_terrain_map_grid
        current_position_room_center_x = self.map_width / 2
        current_position_room_center_y = self.map_height / 2
        current_room_number = 0

        # get room stats
        new_room_width = random.randrange(min_room_width, max_room_width)
        new_room_height = random.randrange(min_room_height, max_room_height)

        # loop through and fill the map with 1s where the room is
        for w in range(new_room_width):
            for h in range(new_room_height):

                ##### Check if the tile is on a wall #####
                number_of_walls_on_tile = 0 # this tile is not a wall. if a tile is a wall, this will be 1. If its a corner, it will be 2.
                if w == 0:
                    # this is a left side wall
                    terrain_map_grid[current_position_room_center_x - (new_room_width / 2) + w][current_position_room_center_y - (new_room_height / 2) + h] = 5
                    number_of_walls_on_tile += 1 # this is a wall
                    
                if h == 0:
                    # this is a up side wall
                    terrain_map_grid[current_position_room_center_x - (new_room_width / 2) + w][current_position_room_center_y - (new_room_height / 2) + h] = 4
                    number_of_walls_on_tile += 1 # this is a wall
                    
                if w == new_room_width - 1:
                    # this is a right side wall
                    terrain_map_grid[current_position_room_center_x - (new_room_width / 2) + w][current_position_room_center_y - (new_room_height / 2) + h] = 3
                    number_of_walls_on_tile += 1 # this is a wall
                    
                if h == new_room_height - 1:  
                    # this is a down wall
                    terrain_map_grid[current_position_room_center_x - (new_room_width / 2) + w][current_position_room_center_y - (new_room_height / 2) + h] = 6
                    number_of_walls_on_tile += 1 # this is a wall

                if number_of_walls_on_tile < 1:
                    # set the floors
                    terrain_map_grid[current_position_room_center_x - (new_room_width / 2) + w][current_position_room_center_y - (new_room_height / 2) + h] = 1

                ##### Block off the corners #####
                if  number_of_walls_on_tile >= 2:
                    terrain_map_grid[current_position_room_center_x - (new_room_width / 2) + w][current_position_room_center_y - (new_room_height / 2) + h] = 2
                    
        '''
        while current_room_number < self.number_of_rooms:
            current_room_number += 1

            # pick a new direction to move in
            direction = self._get_random_direction()
            if direction == 'right':
                

            if direction == 'up':

            if direction == 'left':

            if direction == 'down':
        '''

        return terrain_map_grid
if __name__ == '__main__':
    # general map stats
    map_width = 20
    map_height = 20
    number_of_rooms = 200

    # random rooms stats
    max_room_width = 16
    max_room_height = 16
    min_room_width = 4
    min_room_height = 4
    max_hall_length = 6
    min_hall_length = 2
    
    map_grid = MapGrid(map_width, map_height, number_of_rooms,
                       max_room_width, max_room_height,
                       min_room_width, min_room_height)
    print map_grid.terrain_map_grid
