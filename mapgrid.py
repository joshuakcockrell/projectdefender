##### RANDOM MAP GENERATOR #####
# holds the gravity map, the terrain map, the collision map, etc.
import pygame
import random
import math
import time

# used in the aigrid pending sources to active sources transfer
from collections import deque

def convert_position_to_grid_position(position, tile_size):
    '''
    steps in this algorithm:
    x position:
    31.999
    
    divide by tile size to get a number of tile such as:
    0.99996874999999996
    
    floor the position so it becomes:
    0.0
    
    integer form becomes:
    0

    do the same for the y values

    return [grid_position_x, grid_position_y]
    '''
    # calculate for x position
    float_tile_x = position[0] / tile_size
    floored_tile_x = math.floor(float_tile_x)
    grid_position_x = int(floored_tile_x)

    # do the same for the y position
    float_tile_y = position[1] / tile_size
    floored_tile_y = math.floor(float_tile_y)
    grid_position_y = int(floored_tile_y)

    return [grid_position_x, grid_position_y]

def convert_grid_position_to_position(grid_position, tile_size):
    '''
    goes from [1,2] to [32,64]
    '''
    position_x = grid_position[0] * tile_size
    position_y = grid_position[1] * tile_size

    return [position_x, position_y]

class Vector():
    '''
    Class:
        creates operations to handle vectors such
        as direction, position, and speed
    '''
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self): # used for printing vectors
        return "(%s, %s)"%(self.x, self.y)

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("This "+str(key)+" key is not a vector key!")

    def __sub__(self, o): # subtraction
        return Vector(self.x - o.x, self.y - o.y)

    def length(self): # get length (used for normalize)
        return math.sqrt((self.x**2 + self.y**2)) 

    def normalize(self): # divides a vector by its length
        l = self.length()
        if l != 0:
            return (self.x / l, self.y / l)
        return (0, 0)

class MapGrid():

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

    
##    def _generate_empty_aimap_grid(self, map_width, map_height):
##        '''
##        creates a new 2d array with the given specs
##        '''
##
##        new_map_grid = [] # create our new list
##        for x in range(map_width):
##            new_map_grid.append([]) # add our columns to the array
##            for y in range(map_height):
##                cell = AIGridCell([x,y])
##                new_map_grid[x].append(cell) # fill in our rows
##
##        return new_map_grid
##    
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

    def _set_grid_position_value(self, grid, position, value):
        '''
        sets a position on a grid to a given value,
        used when closing off walls and manually setting values
        '''

        grid[position[0]][position[1]] = value

        return grid

    def _get_grid_position_value(self, grid, position):
        '''
        gets a position on a grid and returns its value
        '''
        try:
            value = grid[position[0]][position[1]]
        except IndexError:
            value = None
        return value

    def get_random_direction(self):
        '''
        generates a random direction,
        used in the random walk algorithm
        '''
        random_direction = random.choice(['right', 'up', 'left', 'down'])

        return random_direction
                    

class CollisionGrid(MapGrid):
    '''
    tiles with a value of 1 are closed
    tiles with a value of 0 are open
    '''
    def __init__(self, map_dimensions):
        self.map_dimensions = map_dimensions
        
        # create a grid which holds the collision tile information
        self.collision_grid = self._generate_empty_map_grid(self.map_dimensions[0], self.map_dimensions[1])

    def close_tile(self, grid_position):
        self.collision_grid = self._set_grid_position_value(self.collision_grid, grid_position, 1)

    def open_tile(self, grid_position):
        self.collision_grid = self._set_grid_position_value(self.collision_grid, grid_position, 0)

    def is_tile_open(self, grid_position):
        value = self._get_grid_position_value(self.collision_grid, grid_position)
        if value == 1:
            # the tile is closed
            return False
        elif value == 0:
            # the tile is open
            return True
        elif value == None:
            return True
        else:
            raise RuntimeError('Incorrect tile value: ' + str(value))

    def get_surrounding_tiles(self, column_index, tile_index):
        '''Goes through all the surrounding tiles, and returns the lowest value of each one'''
                                            
        # get the surrounding tile values for each tile
        x = column_index
        y = tile_index

        # TOP ROW 
        # if too far up
        if y - 1 < 0:
            top_left = None
            top_mid = None
            top_right = None
        else:
            
            # TOP LEFT
            # if too far left 
            if x - 1 < 0:
                top_left = None
            else:
                try:
                    top_left = self.collision_grid[x - 1][y - 1]
                # handle too far right or down
                except IndexError:
                    top_left = None
            

            # TOP MID
            # if too far left
            if x < 0:
                top_mid = None

            else:
                try:
                    top_mid = self.collision_grid[x][y - 1]
                # if too far right or down
                except IndexError:
                    top_mid = None

            # TOP RIGHT
            # if too far left
            if x + 1 < 0:
                top_right = None
            else:
                try:
                    top_right = self.collision_grid[x + 1][y - 1]
                except IndexError:
                    top_right = None
                    
        # CENTER ROW
        # if too far up
        if y < 0:
            center_left = None
            center_mid = None
            center_right = None

        else:
            # CENTER LEFT
            # if too far left
            if x - 1 < 0:
                center_left = None
            else:
                try:
                    center_left = self.collision_grid[x - 1][y]
                    # if too far right or down
                except IndexError:
                    center_left = None

            # CENTER MID
            # if too far left
            if x < 0:
                center_mid = None
            else:
                try:
                    center_mid = self.collision_grid[x][y]
                # if too far right or down
                except IndexError:
                    center_mid = None

            # CENTER RIGHT
            # if too far left
            if x + 1 < 0:
                center_right = None
            else:
                try:
                    center_right = self.collision_grid[x + 1][y]
                # if too far right or down
                except IndexError:
                    center_right = None
                    

        # BOTTOM ROW
        # if too far up
        if y + 1 < 0:
            bottom_left = None
            bottom_mid = None
            bottom_right = None
        else:
            # BOTTOM LEFT
            # if too far left
            if x - 1 < 0:
                bottom_left = None
            else:
                try:
                    bottom_left = self.collision_grid[x - 1][y + 1]
                # if too far right or down
                except IndexError:
                    bottom_left = None

            # BOTTOM MID
            # if too far left
            if x < 0:
                bottom_mid = None
            else:
                try:
                    bottom_mid = self.collision_grid[x][y + 1]
                # if too far right or down
                except IndexError:
                    bottom_mid = None

            # BOTTOM RIGHT
            # if too far left
            if x + 1 < 0:
                bottom_right = None
            else:
                try:
                    bottom_right = self.collision_grid[x + 1][y + 1]
                # if too far right or down
                except IndexError:
                    bottom_right = None
        return (top_left, top_mid, top_right,
                center_left, center_mid, center_right,
                bottom_left, bottom_mid, bottom_right)
    
class TerrainGrid(MapGrid):

    def __init__(self):
        # create a grid which holds the terrain image information
        self.empty_terrain_map_grid = self._generate_empty_map_grid(self.map_width, self.map_height)
        #self.terrain_map_grid = self._generate_terrain_map_random_walk(self.empty_terrain_map_grid)

        self.terrain_map_grid = self._generate_terrain_map_random_rooms(self.empty_terrain_map_grid,
                                                                        number_of_rooms, starting_room_direction,
                                                                        max_room_width, max_room_height,
                                                                        min_room_width, min_room_height,
                                                                        max_hall_length, min_hall_length,
                                                                        room_size_multiplier)
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
            direction = self.get_random_direction()
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
                                           starting_room_direction,
                                           max_room_width, max_room_height,
                                           min_room_width, min_room_height,
                                           max_hall_length, min_hall_length,
                                           room_size_multiplier):
        '''
        fills up our grid with more clearly defined rooms
        room variables:
        0 = empty
        1 = floor
        2 = closed wall (unable to build off of)
        3 = right wall
        4 = up wall
        5 = left wall
        6 = down wall
        7 = testing if stuff works
        '''

        terrain_map_grid = empty_terrain_map_grid
        number_of_rooms = number_of_rooms
        self.current_room_number = 0

        # set our starting room center (middle of the map)
        current_tile_position_x = self.map_width / 2
        current_tile_position_y = self.map_height / 2
        current_tile_position = [current_tile_position_x, current_tile_position_y]

        ##### Create our first room #####
        
        # get room stats
        print 'creating first room'
        new_room_width = random.randrange(min_room_width, max_room_width)
        new_room_height = random.randrange(min_room_height, max_room_height)

        terrain_map_grid = self._append_room_to_terrain_map(terrain_map_grid, current_tile_position,
                                                            new_room_width, new_room_height,
                                                            starting_room_direction)
        self.current_room_number += 1
        
        while self.current_room_number < number_of_rooms:
            print 'making the rest of the rooms'
            ##### Make the rest of the rooms #####

            # get random hall direction
            hall_direction = self.get_random_direction()
            # get next hall starting position
            hall_start_position = self._get_hall_start_position(terrain_map_grid, hall_direction)
            print 'hall start position'
            print hall_start_position
            if hall_start_position != False:

                # get hall distance
                hall_distance = random.randrange(min_hall_length, max_hall_length)
                print 'hall distance'
                print hall_distance
                # get hall end position
                hall_end_position = self._get_hall_end_position(hall_start_position, hall_direction, hall_distance)
                print 'hall end position'
                print hall_end_position

                # get room stats
                room_width = random.randrange(min_room_width, max_room_width)
                room_height = random.randrange(min_room_height, max_room_height)

                # check if area is clear
                if self._area_is_empty_of_terrain(terrain_map_grid, hall_start_position, hall_direction, hall_distance, room_width, room_height, room_size_multiplier):

                    print 'current room number'
                    print self.current_room_number

                    print 'hall end position to append room'
                    print hall_end_position

                    # create and append a room
                    terrain_map_grid = self._append_room_to_terrain_map(terrain_map_grid, hall_end_position,
                                                                        room_width, room_height, hall_direction)

                    # create and append the hallway
                    terrain_map_grid = self._append_hallway_to_terrain_map(terrain_map_grid, hall_start_position, hall_direction, hall_distance)
                    print 'hall distance'
                    print hall_distance

                else:
                    # close the wall
                    print 'CLOSING TILE DUE TO BOUNDARIES'
                    print hall_start_position
                    terrain_grid_map = self._set_terrain_grid_position_value(terrain_map_grid, hall_start_position, 2)
                    print 'hi'
         
                self.current_room_number += 1
        
        return terrain_map_grid

    def _area_is_empty_of_terrain(self, terrain_map_grid, hall_start_position, hall_direction,
                                 hall_distance, room_width, room_height,
                                 room_size_multiplier):
        '''
        returns true if the area is empty of terrain (if the space is filled with 0s
        room_size_multiplier: size of room * room_size_multiplier = size of area to check
        '''
        position_to_check = hall_start_position
        starting_grid_position = [0,0]
        current_grid_position = [0,0]

        # get size to check for right and left rooms
        if hall_direction == 'right':
            width_to_check = (room_width * room_size_multiplier) + hall_distance
            height_to_check = room_height * room_size_multiplier


            # set the top left corner of our area to check
            starting_grid_position[0] = hall_start_position[0] + 1
            starting_grid_position[1] = hall_start_position[1] - (height_to_check / 2)
            
            # round and turn positions into integers
            starting_grid_position[0] = int(round(starting_grid_position[0]))
            starting_grid_position[1] = int(round(starting_grid_position[1]))

            print 'AREA INTERSECTS TERRAIN'
            print 'hall direction'
            print hall_direction
            print 'hall distance'
            print hall_distance
            print 'room width'
            print room_width
            print 'room height'
            print room_height
            print 'width to check'
            print width_to_check
            print 'height to check'
            print height_to_check
            print 'hall starting position'
            print hall_start_position
            print 'starting grid position'
            print starting_grid_position
            
            # go through all the tiles in the space to check and see if they are open
            for x in range(width_to_check):
                for y in range(height_to_check):

                    current_grid_position[0] = starting_grid_position[0] + x
                    current_grid_position[1] = starting_grid_position[1] + y

                    # check if the spot is open
                    print current_grid_position
                    if current_grid_position[0] < 0 or current_grid_position[1] < 0:
                        print 'WERE AT THE EDGE OF THE MAP HERE'
                        print current_grid_position
                        # we are at the edge of the map
                        return False

                    else:
                        # we are not at the top or left of the map, yet..
                        
                        try:
                            if terrain_map_grid[current_grid_position[1]][current_grid_position[0]] == 0:
                                pass
                            else:
                                print 'WERE RUNNING INTO WALLS HERE'
                                print current_grid_position
                                # the spot is closed
                                return False
                        except IndexError:
                            print 'WERE AT THE EDGE OF THE MAP HERE'
                            print current_grid_position
                            # the spot is at the edge of the map
                            return False

        if hall_direction == 'left':
            width_to_check = (room_width * room_size_multiplier) + hall_distance
            height_to_check = room_height * room_size_multiplier

            # set the top left corner of our area to check
            starting_grid_position[0] = (hall_start_position[0] - width_to_check) - 1
            starting_grid_position[1] = hall_start_position[1] - (height_to_check / 2)

            # round and turn positions into integers
            starting_grid_position[0] = int(round(starting_grid_position[0]))
            starting_grid_position[1] = int(round(starting_grid_position[1]))

            print 'AREA INTERSECTS TERRAIN'
            print 'hall direction'
            print hall_direction
            print 'hall distance'
            print hall_distance
            print 'room width'
            print room_width
            print 'room height'
            print room_height
            print 'width to check'
            print width_to_check
            print 'height to check'
            print height_to_check
            print 'hall starting position'
            print hall_start_position
            print 'starting grid position'
            print starting_grid_position

            # go through all the tiles in the space to check and see if they are open
            for x in range(width_to_check):
                for y in range(height_to_check):

                    current_grid_position[0] = starting_grid_position[0] + x
                    current_grid_position[1] = starting_grid_position[1] + y

                    # check if the spot is open
                    print current_grid_position
                    if current_grid_position[0] < 0 or current_grid_position[1] < 0:
                        print 'WERE AT THE EDGE OF THE MAP HERE'
                        print current_grid_position
                        # we are at the edge of the map
                        return False

                    else:
                        # we are not at the top or left of the map, yet..
                        
                        try:
                            if terrain_map_grid[current_grid_position[1]][current_grid_position[0]] == 0:
                                pass
                            else:
                                print 'WERE RUNNING INTO WALLS HERE'
                                print current_grid_position
                                # the spot is closed
                                return False
                        except IndexError:
                            print 'WERE AT THE EDGE OF THE MAP HERE'
                            print current_grid_position
                            # the spot is at the edge of the map
                            return False

        # get size to check for up and down rooms
        elif hall_direction == 'up':
            width_to_check = room_width * room_size_multiplier
            height_to_check = (room_height * room_size_multiplier) + hall_distance

            # set the top left corner of our area to check
            starting_grid_position[0] = hall_start_position[0] - (width_to_check / 2)
            starting_grid_position[1] = (hall_start_position[1] - 1) - height_to_check

            # round and turn positions into integers
            starting_grid_position[0] = int(round(starting_grid_position[0]))
            starting_grid_position[1] = int(round(starting_grid_position[1]))

            print 'AREA INTERSECTS TERRAIN'
            print 'hall direction'
            print hall_direction
            print 'hall distance'
            print hall_distance
            print 'room width'
            print room_width
            print 'room height'
            print room_height
            print 'width to check'
            print width_to_check
            print 'height to check'
            print height_to_check
            print 'hall starting position'
            print hall_start_position
            print 'starting grid position'
            print starting_grid_position

            # go through all the tiles in the space to check and see if they are open
            for x in range(width_to_check):
                for y in range(height_to_check):

                    current_grid_position[0] = starting_grid_position[0] + x
                    current_grid_position[1] = starting_grid_position[1] + y

                    # check if the spot is open
                    print current_grid_position
                    if current_grid_position[0] < 0 or current_grid_position[1] < 0:
                        print 'WERE AT THE EDGE OF THE MAP HERE'
                        print current_grid_position
                        # we are at the edge of the map
                        return False

                    else:
                        # we are not at the top or left of the map, yet..
                        
                        try:
                            if terrain_map_grid[current_grid_position[1]][current_grid_position[0]] == 0:
                                pass
                            else:
                                print 'WERE RUNNING INTO WALLS HERE'
                                print current_grid_position
                                # the spot is closed
                                return False
                        except IndexError:
                            print 'WERE AT THE EDGE OF THE MAP HERE'
                            print current_grid_position
                            # the spot is at the edge of the map
                            return False

        elif hall_direction == 'down':
            width_to_check = room_width * room_size_multiplier
            height_to_check = (room_height * room_size_multiplier) + hall_distance

            # set the top left corner of our area to check
            starting_grid_position[0] = hall_start_position[0] - (width_to_check / 2)
            starting_grid_position[1] = hall_start_position[1] + 1

            # round and turn positions into integers
            starting_grid_position[0] = int(round(starting_grid_position[0]))
            starting_grid_position[1] = int(round(starting_grid_position[1]))

            print 'AREA INTERSECTS TERRAIN'
            print 'hall direction'
            print hall_direction
            print 'hall distance'
            print hall_distance
            print 'room width'
            print room_width
            print 'room height'
            print room_height
            print 'width to check'
            print width_to_check
            print 'height to check'
            print height_to_check
            print 'hall starting position'
            print hall_start_position
            print 'starting grid position'
            print starting_grid_position

            # go through all the tiles in the space to check and see if they are open
            for x in range(width_to_check):
                for y in range(height_to_check):

                    current_grid_position[0] = starting_grid_position[0] + x
                    current_grid_position[1] = starting_grid_position[1] + y

                    # check if the spot is open
                    print current_grid_position
                    if current_grid_position[0] < 0 or current_grid_position[1] < 0:
                        print 'WERE AT THE EDGE OF THE MAP HERE'
                        print current_grid_position
                        # we are at the edge of the map
                        return False

                    else:
                        # we are not at the top or left of the map, yet..
                        
                        try:
                            if terrain_map_grid[current_grid_position[1]][current_grid_position[0]] == 0:
                                pass
                            else:
                                print 'WERE RUNNING INTO WALLS HERE'
                                print current_grid_position
                                # the spot is closed
                                return False
                        except IndexError:
                            print 'WERE AT THE EDGE OF THE MAP HERE'
                            print current_grid_position
                            # the spot is at the edge of the map
                            return False
                    
        # if it has not returned False, then...
        print 'THERE ARE NO WALLS WERE RUNNING INTO'
        return True

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
                    print 'hall wants to start on direction:'
                    print direction
                    start_position = [column_index, tile_index]
                    print 'start position generated'
                    print start_position
                    return start_position

        # we did not find any rooms with that direction available
        return False
                
    def _get_hall_end_position(self, hall_start_position, hall_direction, hall_distance):
        '''
        uses the hall start position and the hall end position
        to get the ending hall position
        '''
        print 'hall starting position in hall end position function'
        print hall_start_position
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
        


    def _append_room_to_terrain_map(self, terrain_map_grid, hall_end_position, 
                                    room_width, room_height, direction):
        '''
        Adds the room specs to the terrain map grid.
        direction = which side the room is on in relation to the current_room_position
        '''
        
        room_starting_position = [0,0]
        current_grid_position = [0,0]

        print 'in append room to terrain map'
        print hall_end_position
        print room_width
        print room_height
        print direction

        # set the top left starting positions
        if direction == 'center':
            room_starting_position[0] = hall_end_position[0] - (room_width / 2)
            room_starting_position[1] = hall_end_position[1] - (room_height / 2)

        elif direction == 'right':
            room_starting_position[0] = hall_end_position[0]
            room_starting_position[1] = hall_end_position[1] - (room_height / 2)

        elif direction == 'up':
            room_starting_position[0] = hall_end_position[0] - (room_width / 2)
            room_starting_position[1] = (hall_end_position[1] - room_height) + 1

        elif direction == 'left':
            room_starting_position[0] = (hall_end_position[0] - room_width) + 1
            room_starting_position[1] = hall_end_position[1] - (room_height / 2)

        elif direction == 'down':
            room_starting_position[0] = hall_end_position[0] - (room_width / 2)
            room_starting_position[1] = hall_end_position[1]
        print 'room top left position'
        print room_starting_position

        for x in range(room_width):
            for y in range(room_height):
                
                current_grid_position[0] = room_starting_position[0] + x
                current_grid_position[1] = room_starting_position[1] + y
                
                # this tile is not a wall. if a tile is a wall, this will be 1. If its a corner, it will be 2.
                number_of_walls_on_tile = 0

                # this is a left side wall
                if x == 0:
                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 5
                    number_of_walls_on_tile += 1 # this is a wall

                # this is a up side wall
                if y == 0:
                    print 'ISSUES HERE'
                    print current_grid_position
                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 4
                    number_of_walls_on_tile += 1 # this is a wall

                # this is a right side wall
                if x == room_width - 1:
                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 3
                    number_of_walls_on_tile += 1 # this is a wall

                # this is a down wall
                if y == room_height - 1:  
                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 6
                    number_of_walls_on_tile += 1 # this is a wall

                # set the floors
                if number_of_walls_on_tile < 1:
                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 1

                # block off the corners so we cannot build halls there
                if  number_of_walls_on_tile >= 2:
                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 2

        return terrain_map_grid
    

    def _append_hallway_to_terrain_map(self, terrain_map_grid, hall_start_position,
                                       hall_direction, hall_distance):
        '''
        Adds the room specs to the terrain map grid.
        direction = which side the hallway is on in relation to the hall_start_position
        '''
        
        starting_grid_position = [0,0]
        current_grid_position = [0,0]
        starting_grid_position[0] = hall_start_position[0]
        starting_grid_position[1] = hall_start_position[1]
        hall_width = 1
        print 'hall start position'
        print starting_grid_position
        print 'hall direction'
        print hall_direction

        # add one to compensate for lists starting at 0
        hall_distance += 1

        # right hallways
        if hall_direction == 'right':
            width_to_fill = hall_distance
            height_to_fill = hall_width

            for x in range(hall_distance):
                for y in range(hall_width):

                    current_grid_position[0] = starting_grid_position[0] + x
                    current_grid_position[1] = starting_grid_position[1] + y

                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 7

        # up hallways
        elif hall_direction == 'up':
            width_to_fill = 1
            height_to_fill = hall_distance

            for x in range(hall_width):
                for y in range(hall_distance):

                    current_grid_position[0] = starting_grid_position[0] - x
                    current_grid_position[1] = starting_grid_position[1] - y

                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 7

        # left hallways
        elif hall_direction == 'left':
            width_to_fill = hall_distance
            height_to_fill = 1

            for x in range(hall_distance):
                for y in range(hall_width):

                    current_grid_position[0] = starting_grid_position[0] - x
                    current_grid_position[1] = starting_grid_position[1] - y

                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 7

        # down hallways
        elif hall_direction == 'down':
            width_to_fill = 1
            height_to_fill = hall_distance

            for x in range(hall_width):
                for y in range(hall_distance):

                    current_grid_position[0] = starting_grid_position[0] + x
                    current_grid_position[1] = starting_grid_position[1] + y

                    terrain_map_grid[current_grid_position[0]][current_grid_position[1]] = 7

        else:
            print 'Invalid hallway direction in _append_hallway_to_terrain_map...'
            
        return terrain_map_grid

class OutsideTerrainGrid(MapGrid):
    def __init__(self, map_dimensions):

        # generate outside rooms
        self.empty_outside_terrain_grid = self._generate_empty_noise_grid(self.map_width, self.map_height)
        self.outside_terrain_grid = self._generate_outside_terrain(self.empty_outside_terrain_grid, number_of_generations)

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

    
class GravityGrid(MapGrid):
    def __init__(self, map_dimensions):

        # create a grid which holds the gravitational tile information
        self.gravity_map_grid = self._generate_empty_gravity_map_grid(self.map_width, self.map_height)

        #gravity_map_grid, gravity_position, radius, force_denometer
        self.gravity_map_grid = self._add_gravity_point(self.gravity_map_grid, [4,4], 5, 1)
        #print self.gravity_map_grid

    def _generate_empty_gravity_map_grid(self, map_width, map_height):
        '''
        creates a new 2d array with the given specs
        '''

        new_map_grid = [] # create our new list
        for x in range(map_width):
            new_map_grid.append([]) # add our columns to the array
            for y in range(map_height):
                # fill the grid with empty:
                #[[velocity], force]
                new_map_grid[x].append([[0.0,0.0], 0]) # fill in our rows
                

        return new_map_grid

    def _add_gravity_point(self, gravity_map_grid, gravity_position, radius, force_denometer):
        gravity_position_vector = Vector(gravity_position[0], gravity_position[1])
        diameter_to_check = radius * 2
        # set the top left position to check
        starting_position = [gravity_position[0] - radius, gravity_position[1] - radius]
        current_position = [0,0]
        for current_column in range(diameter_to_check):
            for current_tile in range(diameter_to_check):
                current_position = [starting_position[0] + current_tile,
                                    starting_position[1] + current_column]
                current_position_vector = Vector(current_position[0], current_position[1])
                # get the distance to the gravity position
                distance_to_gravity_position= gravity_position_vector - current_position_vector
                # normalize the vector
                normalized_distance = distance_to_gravity_position.normalize()
                if normalized_distance == None:
                    normalized_distance = [0.0,0.0]

                length_to_gravity_position = distance_to_gravity_position.length()
                force_of_gravity = length_to_gravity_position / force_denometer

                # for testing purposes when using a text output

                rounded_x_distance = int(round(normalized_distance[0] * 10)) / 10
                rounded_y_distance = int(round(normalized_distance[1] * 10)) / 10
                normalized_distance = [rounded_x_distance, rounded_y_distance]

                force_of_gravity = int(round(force_of_gravity * 10)) / 10

                gravity_map_grid[current_position[0]][current_position[1]] = [normalized_distance, force_of_gravity]

        return gravity_map_grid

##
##class AIGridCell():
##    ''' There is exactly one of these for every position on our grid
##
##    It can be accessed by AIGrid.grid[x][y]
##    (which returns one of these objects)
##
##    values are stored in the self.values list in the format
##    self.values = [(owner, value), (owner, value)...]
##    with the lowest value being stored first
##
##    '''
##    def __init__(self, grid_position):
##        self.grid_position = grid_position
##        self.values = []
##
##    def __repr__(self):
##        if self.values:
##            return str(self.values[0][1])
##        else:
##            return str(0)
##        
##    def get_owner_value(self, owner):
##        '''Return the value that this owner_id has'''
##        
##        for v in self.values:
##            # if the owner has a value in our values list
##            if owner == v[0]:
##                return v[1]
##        return 0
##
##    def remove_child(self, primary_source):
##        '''Removes a value belonging to the owner who wants it removed'''
##        for i, v in enumerate(self.values):
##            if v[0] == primary_source:
##                self.values.pop(i)
##                break
##
##    def get_lowest_tile(self):
##        '''Returns the lowest tile in our list'''
##        if self.values:
##            return self.values[0][1]
##        else:
##            # zero if its not there
##            return 0
##
##    def add_value(self, value):
##        '''This adds a value to the self.values list, and keeps the list sorted'''
##        
##        number_of_values = len(self.values) # get num of values
##        for i in range(0, number_of_values): # go through all the values
##            if value[1] < self.values[i][1]: # if the new value is less than on in the list
##                self.values.insert(i, value) # put the new value there
##                break
##            else: # if its greater
##                # if were at the end of the list
##                if i == (number_of_values - 1):
##                    self.values.append(value) # add it to the end of the list
##        # if its the first element
##        if self.values == []:
##            self.values.append(value) # add it to the list
##
##        
##class AIGridSource():
##    ''' This is an edge of the current flood fill algorithm
##    It is used to know where we need to update our grid at'''
##    
##    def __init__(self, grid_position, strength, max_generations, next_generation, primary_source):
##        self.grid_position = grid_position
##        self.max_generations = max_generations
##        self.current_generation = next_generation
##        self.strength = strength # how much the sources children will be incremented by
##        self.primary_source = primary_source
##        self.values = []
##
##    def update_values(self, grid_position, strength, max_generations, next_generation, primary_source):
##        self.grid_position = grid_position
##        self.max_generations = max_generations
##        self.current_generation = next_generation
##        self.strength = strength
##        self.primary_source = primary_source

def run_test():
    pass
    

##class AIGrid(MapGrid):
##    def __init__(self, map_dimensions):
##        ''' This holds the movement priority list for the AI
##
##        This uses a floodfill algorithm to fill the grid
##
##        0 = Not yet assigned enemies will not go here
##        1 = target enemies will reach the closest one of these
##        2 - infinite = enemies will look for the nearest lower number
##
##        how this will work
##        add source to grid
##
##        every frame
##        tiles tagged as uncomplete use as source, source spawns sources
##
##        for nearby
##        if nearby is == to source
##        end source
##
##        if nearby are higher than source + 1
##        then make nearby source + 1
##        end source
##        make new source at nearby
##
##        if nearby are lower than source
##        can nearby be lower than source - 1?
##        end source
##        
##        '''
##        self.map_dimensions = map_dimensions
##        self.active_sources = []
##        self.pending_active_sources = []
##        self.cached_sources = deque()
##        self.sources_to_be_depreciated = []
##
##        
##        # create a grid which holds the flood fill AI influence map
##        #self.grid = self._generate_empty_map_grid(self.map_dimensions[0], self.map_dimensions[1])
##        self.grid = self._generate_empty_aimap_grid(self.map_dimensions[0], self.map_dimensions[1])
##
##    def add_source_to_grid(self, center_grid_position, strength, max_generations, next_generation, primary_source):
##        '''creates a source object and adds it to our list to be updated'''
##        # get a cached source
##        ai_grid_source = self.get_cached_source(center_grid_position, strength, max_generations, next_generation, primary_source)
##
##        # add the source to pending so it will be updated
##        self.pending_active_sources.append(ai_grid_source)
##
##        # tell the primary_source that it has a child so it can get rid of it if necessary.
##        primary_source.add_ai_child_position([center_grid_position[0],center_grid_position[1]])
##
##        # set the value of the grid cell
##        value = (primary_source, next_generation * strength)
##        self.grid[center_grid_position[0]][center_grid_position[1]].add_value(value)
##
##    def get_cached_source(self, center_grid_position, strength, max_generations, next_generation, primary_source):
##        ''' returns the first cached source (if there is one) '''
##
##        # if there are any in the cache
##        if self.cached_sources:
##            source = self.cached_sources.popleft()
##            # update the source values
##            source.update_values(center_grid_position, strength, max_generations, next_generation, primary_source)
##            
##        else:
##            # or create a new one
##            source = AIGridSource(center_grid_position, strength, max_generations, next_generation, primary_source)
##
##        return source
##
##
##    def remove_target_from_grid(self, center_grid_position):
##        raise RuntimeError('HOLY CRAP WHAT DOES THIS FUNCTION DO!!!!')
##        self.grid[center_grid_position[0]][center_grid_position[1]] = 0
##
##    def remove_child(self, primary_source, position):
##        self.grid[position[0]][position[1]].remove_child(primary_source)
##
##    def get_position_value(self, grid_position):
##        position_cell = self.grid[grid_position[0]][grid_position[1]]
##        return position_cell.get_lowest_tile()
##
##    def get_target_grid_position(self, center_grid_position):
##
##        # get all 9 nearby tiles
##        (top_left, top_mid, top_right,
##         center_left, center_mid, center_right,
##         bottom_left, bottom_mid, bottom_right) = self._get_surrounding_lowest_tiles(center_grid_position[0], center_grid_position[1])
##
##        # sort them so we know which is the least
##        tiles = [['top left', top_left], ['top mid', top_mid], ['top right', top_right],
##                 ['center left', center_left], ['center mid', center_mid], ['center right', center_right],
##                 ['bottom left', bottom_left], ['bottom mid', bottom_mid], ['bottom right' , bottom_right]]
##
##        # get rid of all the tiles with the value of zero
##        good_indexes = []
##        good_tiles = []
##        for i, t in enumerate(tiles):
##            if t[1] > 0:
##                good_indexes.append(i)
##        for i in good_indexes:
##            good_tiles.append(tiles[i])
##        tiles = good_tiles
##
##        # sort the tiles into lowest first
##        sorted_tiles = sorted(tiles, key=lambda tile: tile[1])
##
##        target_value = 0
##        target_destination = None
##        
##        if len(sorted_tiles) >= 1: # if any tiles exist in the list
##                
##            # decide what tile is the target
##            x = center_grid_position[0]
##            y = center_grid_position[1]
##            if sorted_tiles[0][0] == 'top left':
##                target_tile = [x - 1, y - 1]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'top mid':
##                target_tile = [x, y - 1]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'top right':
##                target_tile = [x + 1, y - 1]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'center left':
##                target_tile = [x - 1, y]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'center mid':
##                target_tile = [x, y]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'center right':
##                target_tile = [x + 1, y]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'bottom left':
##                target_tile = [x - 1, y + 1]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'bottom mid':
##                target_tile = [x, y + 1]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            elif sorted_tiles[0][0] == 'bottom right':
##                target_tile = [x + 1, y + 1]
##                target_value = sorted_tiles[0][1]
##                target_destination = sorted_tiles[0][0]
##            else:
##                raise Exception('Tiles sorted incorrectly! ' + str(sorted_tiles))
##        else:
##            target_tile = None
##
##        return target_tile
##
##    def update(self):
##        ''' Goes through all the active sources and updates their surroundings'''
##
##        self.active_sources.extend(self.pending_active_sources) # move our pending to our active
##        self.cached_sources.extend(self.sources_to_be_depreciated) # cache the depreciated sources
##        self.pending_active_sources = [] # clear the pending list
##        self.sources_to_be_depreciated = [] # clear the depreciated lists
##        
##        for s in self.active_sources:
##            next_generation = s.current_generation + 1
##            if next_generation <= s.max_generations:
##                x = s.grid_position[0]
##                y = s.grid_position[1]
##                source_value = s.current_generation * s.strength
##                                
##                # get all 9 nearby tiles
##                (top_left, top_mid, top_right,
##                 center_left, center_mid, center_right,
##                 bottom_left, bottom_mid, bottom_right) = self._get_surrounding_owner_tiles(x, y, s.primary_source)
##                # top mid
##                # if the owner value is more than the next value
##                if top_mid > (source_value + s.strength) or top_mid == 0:
##                    self.add_source_to_grid([x, y - 1], s.strength, s.max_generations, next_generation, s.primary_source)
##
##                # center left
##                if center_left > (source_value + s.strength) or center_left == 0:
##                    self.add_source_to_grid([x - 1, y], s.strength, s.max_generations, next_generation, s.primary_source)
##   
##                # center right        
##                if center_right > (source_value + s.strength) or center_right == 0:
##                    self.add_source_to_grid([x + 1, y], s.strength, s.max_generations, next_generation, s.primary_source)
##                    
##                # bottom mid      
##                if bottom_mid > (source_value + s.strength) or bottom_mid == 0:
##                    self.add_source_to_grid([x, y + 1], s.strength, s.max_generations, next_generation, s.primary_source)
##
##            self.sources_to_be_depreciated.append(s)
##        self.active_sources = []
##        
##        #print self.grid
##
##    def _get_surrounding_lowest_tiles(self, column_index, tile_index):
##        '''Goes through all the surrounding tiles, and returns the lowest value of each one'''
##                                            
##        # get the surrounding tile values for each tile
##        x = column_index
##        y = tile_index
##
##        ##### TOP ROW #####
##            
##        # if too far up
##        if y - 1 < 0:
##            top_left = None
##            top_mid = None
##            top_right = None
##        else:
##            
##            # TOP LEFT
##            # if too far left 
##            if x - 1 < 0:
##                top_left = None
##            else:
##                try:
##                    top_left = self.grid[x - 1][y - 1].get_lowest_tile()
##                # handle too far right or down
##                except IndexError:
##                    top_left = None
##            
##
##            # TOP MID
##            # if too far left
##            if x < 0:
##                top_mid = None
##
##            else:
##                try:
##                    top_mid = self.grid[x][y - 1].get_lowest_tile()
##                # if too far right or down
##                except IndexError:
##                    top_mid = None
##
##            # TOP RIGHT
##            # if too far left
##            if x + 1 < 0:
##                top_right = None
##            else:
##                try:
##                    top_right = self.grid[x + 1][y - 1].get_lowest_tile()
##                except IndexError:
##                    top_right = None
##                    
##
##        ##### CENTER ROW #####
##
##        # if too far up
##        if y < 0:
##            center_left = None
##            center_mid = None
##            center_right = None
##
##        else:
##            # CENTER LEFT
##            # if too far left
##            if x - 1 < 0:
##                center_left = None
##            else:
##                try:
##                    center_left = self.grid[x - 1][y].get_lowest_tile()
##                    # if too far right or down
##                except IndexError:
##                    center_left = None
##
##            # CENTER MID
##            # if too far left
##            if x < 0:
##                center_mid = None
##            else:
##                try:
##                    center_mid = self.grid[x][y].get_lowest_tile()
##                # if too far right or down
##                except IndexError:
##                    center_mid = None
##
##            # CENTER RIGHT
##            # if too far left
##            if x + 1 < 0:
##                center_right = None
##            else:
##                try:
##                    center_right = self.grid[x + 1][y].get_lowest_tile()
##                # if too far right or down
##                except IndexError:
##                    center_right = None
##                    
##
##        ##### BOTTOM ROW #####
##
##        # if too far up
##        if y + 1 < 0:
##            bottom_left = None
##            bottom_mid = None
##            bottom_right = None
##        else:
##            # BOTTOM LEFT
##            # if too far left
##            if x - 1 < 0:
##                bottom_left = None
##            else:
##                try:
##                    bottom_left = self.grid[x - 1][y + 1].get_lowest_tile()
##                # if too far right or down
##                except IndexError:
##                    bottom_left = None
##
##            # BOTTOM MID
##            # if too far left
##            if x < 0:
##                bottom_mid = None
##            else:
##                try:
##                    bottom_mid = self.grid[x][y + 1].get_lowest_tile()
##                # if too far right or down
##                except IndexError:
##                    bottom_mid = None
##
##            # BOTTOM RIGHT
##            # if too far left
##            if x + 1 < 0:
##                bottom_right = None
##            else:
##                try:
##                    bottom_right = self.grid[x + 1][y + 1].get_lowest_tile()
##                # if too far right or down
##                except IndexError:
##                    bottom_right = None
##        return (top_left, top_mid, top_right,
##                center_left, center_mid, center_right,
##                bottom_left, bottom_mid, bottom_right)
##
##    def _get_surrounding_owner_tiles(self, column_index, tile_index, owner_id):
##        '''Goes through all the surrounding tiles, and returns the value with the owner_id specified'''
##                                            
##        # get the surrounding tile values for each tile
##        x = column_index
##        y = tile_index
##
##        ##### TOP ROW #####
##            
##        # if too far up
##        if y - 1 < 0:
##            top_left = None
##            top_mid = None
##            top_right = None
##        else:
##            
##            # TOP LEFT
##            # if too far left 
##            if x - 1 < 0:
##                top_left = None
##            else:
##                try:
##                    top_left = self.grid[x - 1][y - 1].get_owner_value(owner_id)
##
##                # handle too far right or down
##                except IndexError:
##                    top_left = None
##            
##
##            # TOP MID
##            # if too far left
##            if x < 0:
##                top_mid = None
##
##            else:
##                try:
##                    top_mid = self.grid[x][y - 1].get_owner_value(owner_id)
##                # if too far right or down
##                except IndexError:
##                    top_mid = None
##
##            # TOP RIGHT
##            # if too far left
##            if x + 1 < 0:
##                top_right = None
##            else:
##                try:
##                    top_right = self.grid[x + 1][y - 1].get_owner_value(owner_id)
##                except IndexError:
##                    top_right = None
##                    
##
##        ##### CENTER ROW #####
##
##        # if too far up
##        if y < 0:
##            center_left = None
##            center_mid = None
##            center_right = None
##
##        else:
##            # CENTER LEFT
##            # if too far left
##            if x - 1 < 0:
##                center_left = None
##            else:
##                try:
##                    center_left = self.grid[x - 1][y].get_owner_value(owner_id)
##                    # if too far right or down
##                except IndexError:
##                    center_left = None
##
##            # CENTER MID
##            # if too far left
##            if x < 0:
##                center_mid = None
##            else:
##                try:
##                    center_mid = self.grid[x][y].get_owner_value(owner_id)
##                # if too far right or down
##                except IndexError:
##                    center_mid = None
##
##            # CENTER RIGHT
##            # if too far left
##            if x + 1 < 0:
##                center_right = None
##            else:
##                try:
##                    center_right = self.grid[x + 1][y].get_owner_value(owner_id)
##                # if too far right or down
##                except IndexError:
##                    center_right = None
##                    
##
##        ##### BOTTOM ROW #####
##
##        # if too far up
##        if y + 1 < 0:
##            bottom_left = None
##            bottom_mid = None
##            bottom_right = None
##        else:
##            # BOTTOM LEFT
##            # if too far left
##            if x - 1 < 0:
##                bottom_left = None
##            else:
##                try:
##                    bottom_left = self.grid[x - 1][y + 1].get_owner_value(owner_id)
##                # if too far right or down
##                except IndexError:
##                    bottom_left = None
##
##            # BOTTOM MID
##            # if too far left
##            if x < 0:
##                bottom_mid = None
##            else:
##                try:
##                    bottom_mid = self.grid[x][y + 1].get_owner_value(owner_id)
##                # if too far right or down
##                except IndexError:
##                    bottom_mid = None
##
##            # BOTTOM RIGHT
##            # if too far left
##            if x + 1 < 0:
##                bottom_right = None
##            else:
##                try:
##                    bottom_right = self.grid[x + 1][y + 1].get_owner_value(owner_id)
##                # if too far right or down
##                except IndexError:
##                    bottom_right = None
##        return (top_left, top_mid, top_right,
##                center_left, center_mid, center_right,
##                bottom_left, bottom_mid, bottom_right)
                                            
        
class MapGrid():
    def __init__(self, map_width, map_height, number_of_rooms,
                 starting_room_direction,
                 max_room_width, max_room_height,
                 min_room_width, min_room_height,
                 max_hall_length, min_hall_length,
                 room_size_multiplier, number_of_generations):

        self.number_of_rooms = number_of_rooms
        self.map_width = map_width
        self.map_height = map_width
    



                    
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
    
    map_grid = MapGrid(map_width, map_height, number_of_rooms,
                       starting_room_direction,
                       max_room_width, max_room_height,
                       min_room_width, min_room_height,
                       max_hall_length, min_hall_length,
                       room_size_multiplier, number_of_generations)

    #print map_grid.outside_terrain_grid

    pygame.init()

    screen = pygame.display.set_mode((map_width * tile_size,map_height * tile_size))

    one_tile = pygame.Surface((tile_size, tile_size))
    one_tile.fill((0,0,0))
    zero_tile = pygame.Surface((tile_size, tile_size))
    zero_tile.fill((255,255,255))
    colors = {0: zero_tile, 1: one_tile}

    background = pygame.Surface((map_width * tile_size,map_height * tile_size))

    clock = pygame.time.Clock()

    first_gen = True
    
    running = True
    while running == True:
        clock.tick(2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if first_gen:
            themap = map_grid.outside_terrain_grid
            first_gen = False
        else:
            themap = map_grid._generate_outside_terrain(themap, 1)

        for column_index, column in enumerate(themap):
            for tile_index, tile in enumerate(column):
                screen.blit(colors[tile], (tile_index * tile_size, column_index * tile_size))

        pygame.display.flip()

    pygame.quit()
            
    
