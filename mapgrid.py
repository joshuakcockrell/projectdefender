##### RANDOM MAP GENERATOR #####

import random

class MapGrid():
    def __init__(self, map_width, map_height, number_of_rooms,
                 max_room_width, max_room_height,
                 min_room_width, min_room_height,
                 max_hall_length, min_hall_length):

        self.number_of_rooms = number_of_rooms
        self.map_width = map_width
        self.map_height = map_width

        # create a grid which holds the terrain image information
        self.empty_terrain_map_grid = self._generate_new_empty_map_grid(self.map_width, self.map_height)
        #self.terrain_map_grid = self._generate_terrain_map_random_walk(self.empty_terrain_map_grid)

        self.terrain_map_grid = self._generate_terrain_map_random_rooms(self.empty_terrain_map_grid,
                                                                        number_of_rooms,
                                                                        max_room_width, max_room_height,
                                                                        min_room_width, min_room_height,
                                                                        max_hall_length, min_hall_length)
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
        for x in range(map_width):
            new_map_grid.append([]) # add our columns to the array
            for y in range(map_height):
                new_map_grid[x].append(0) # fill in our rows

        return new_map_grid

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

    def _generate_terrain_map_random_rooms(self, empty_terrain_map_grid, number_of_rooms,
                                           max_room_width, max_room_height,
                                           min_room_width, min_room_height,
                                           max_hall_length, min_hall_length):
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
        number_of_rooms = number_of_rooms
        current_room_number = 0

        # set our starting room center (middle of the map)
        current_tile_position_x = self.map_width / 2
        current_tile_position_y = self.map_height / 2
        current_tile_position = [current_tile_position_x, current_tile_position_y]

        ##### Create our first room #####
        
        # get room stats
        new_room_width = random.randrange(min_room_width, max_room_width)
        new_room_height = random.randrange(min_room_height, max_room_height)

        terrain_map_grid = self._append_room_to_terrain_map(terrain_map_grid, current_tile_position,
                                                            new_room_width, new_room_height)
        current_room_number += 1
        
        while current_room_number < number_of_rooms:
            ##### Make the rest of the rooms #####

            # get next starting room position
            hall_direction = self._get_random_direction()
            hall_start_position = self._get_hall_start_position(terrain_map_grid, hall_direction)

            # create a hall
            hall_distance = random.randrange(min_hall_length, max_hall_length)
            hall_end_position = self._get_hall_end_position(hall_start_position, hall_direction, hall_distance)
            
            if self._hall_intersects_terrain(hall_start_position, hall_direction, hall_distance):
                print 'crossing over an already'
            # get room stats
            new_room_width = random.randrange(min_room_width, max_room_width)
            new_room_height = random.randrange(min_room_height, max_room_height)

            # create and append a room
            print hall_start_position
            print hall_end_position
            terrain_map_grid = self._append_room_to_terrain_map(terrain_map_grid, hall_end_position,
                                                                new_room_width, new_room_height)
            current_room_number += 1
        
        return terrain_map_grid

    def _get_hall_start_position(self, terrain_map_grid, direction):
        '''
        goes through the terrain grid and returns positions of walls that
        use the given direction.
        '''
        directions = {'right': 3, 'up': 4, 'left': 5, 'down': 6}
        # loop through the terrain map
        for column_index, column in enumerate(terrain_map_grid):
            for tile_index, tile_value in enumerate(column):
                # check if the current tile is correct for the direction we want to move
                if tile_value == directions[direction]:
                    start_position = [column_index, tile_index]
                    print column
                    print 'hi'
                    print direction
                    print start_position
                    return start_position
                
    def _get_hall_end_position(self, hall_start_position, hall_direction, hall_distance):
        '''
        uses the hall start position and the hall end position
        to get the ending hall position
        '''
        if hall_direction == 'right':
            # get the end position to the right
            hall_end_position = [hall_start_position[0] + hall_distance, hall_start_position[1]]
        elif hall_direction == 'up':
            # get the end position to the up
            hall_end_position = [hall_start_position[0], hall_start_position[1] - hall_distance]
        elif hall_direction == 'left':
            # get the end position to the left
            hall_end_position = [hall_start_position[0] - hall_distance, hall_start_position[1]]
        elif hall_direction == 'down':
            # get the end position to the down
            hall_end_position = [hall_start_position[0], hall_start_position[1] + hall_distance]
            
        return hall_end_position

    def _hall_intersects_terrain(self, hall_start_position, hall_direction, hall_distance):
        '''
        returns true if the hall is colliding with terrain
        '''
        position_to_check = hall_start_position
        hall_intersects_terrain = False
        return False
        '''
        for x in range(hall_distance):
            if hall_direction == 'right':

        elif hall_direction == 'up':

        elif hall_direction == 'left':
            
        elif hall_direction == 'down':
            
            position_to_check = hall_end_position
        '''

    def _get_random_direction(self):
        '''
        generates a random direction,
        used in the random walk algorithm
        '''
        random_direction = random.choice(['right', 'up', 'left', 'down'])

        return random_direction
        

    def _append_room_to_terrain_map(self, terrain_map_grid, current_room_position,
                                    new_room_width, new_room_height):
        '''
        Adds the room specs to the terrain map grid.
        '''
        # loop through and fill the map with tiles where the room is
        for x in range(new_room_width):
            for y in range(new_room_height):

                ##### Decide what kind of tile we will make it #####
                # make an empty position list
                current_tile_position = [0,0]
                number_of_walls_on_tile = 0 # this tile is not a wall. if a tile is a wall, this will be 1. If its a corner, it will be 2.
                current_tile_position[0] = current_room_position[0] - (new_room_width / 2) + x
                current_tile_position[1] = current_room_position[1] - (new_room_height / 2) + y
                if x == 0:
                    # this is a left side wall
                    terrain_map_grid[current_tile_position[0]][current_tile_position[1]] = 5
                    number_of_walls_on_tile += 1 # this is a wall
                    
                if y == 0:
                    # this is a up side wall
                    terrain_map_grid[current_tile_position[0]][current_tile_position[1]] = 4
                    number_of_walls_on_tile += 1 # this is a wall
                    
                if x == new_room_width - 1:
                    # this is a right side wall
                    terrain_map_grid[current_tile_position[0]][current_tile_position[1]] = 3
                    number_of_walls_on_tile += 1 # this is a wall
                    
                if y == new_room_height - 1:  
                    # this is a down wall
                    terrain_map_grid[current_tile_position[0]][current_tile_position[1]] = 6
                    number_of_walls_on_tile += 1 # this is a wall

                if number_of_walls_on_tile < 1:
                    # set the floors
                    terrain_map_grid[current_tile_position[0]][current_tile_position[1]] = 1

                ##### Block off the corners #####
                if  number_of_walls_on_tile >= 2:
                    terrain_map_grid[current_tile_position[0]][current_tile_position[1]] = 2

        return terrain_map_grid




                    
if __name__ == '__main__':
    # general map stats
    map_width = 20
    map_height = 20
    number_of_rooms = 3

    # random rooms stats
    max_room_width = 4
    max_room_height = 4
    min_room_width = 3
    min_room_height = 3
    max_hall_length = 4
    min_hall_length = 3
    
    map_grid = MapGrid(map_width, map_height, number_of_rooms,
                       max_room_width, max_room_height,
                       min_room_width, min_room_height,
                       max_hall_length, min_hall_length)
    print map_grid.terrain_map_grid
