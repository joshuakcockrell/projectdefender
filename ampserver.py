# twisted imports
from twisted.internet import reactor

# python imports
import time
import random

# defender imports
import serverfactory
import events
import mapgrid


class ProgramClock():
    '''
    sends events to the event manager to update all event listeners
    uses python time.time() to get the delta time.
    The delta time (change in time since the last current time) is
    sent to the TickEvent. Different parts of the program use delta
    time to determine how far ahead it needs to step
    (this is used especially in the game physics)
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)
            
        self.initial_time = time.time()
        self.current_time = self.initial_time
        self.FPS = 60.0

        self.running = True


    def run(self):
        if self.running == True:
            reactor.callLater((1.0 / self.FPS), self.run)
        else:
            pass

        self.last_time = self.current_time
        self.current_time = time.time()
        self.delta_time = self.current_time - self.last_time # get delta time

        event = events.TickEvent(self.delta_time)
        self.eventManager.post(event)

    def _stop(self):
        self.running = False

    def notify(self, event):
        if event.name == 'Program Quit Event':
            self._stop()
            

class EnemyGenerator():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        
        self.spawn_position = (500, 500)
        self.spawn_timer = 2 # seconds between spawns
        self.current_spawn_timer = 0 # starts at 0
        self.max_enemies = 1
        self.created_enemies = 0

    def _get_spawn_position(self):
        return self.spawn_position

    def _reset_spawn_timer(self):
        self.current_spawn_timer = 0

    def _create_enemy(self):
        event = events.AddEnemyToGameRequestEvent(self._get_spawn_position())
        self.eventManager.post(event)

    def update(self, delta_time):
        # called by the server state
        self.current_spawn_timer += delta_time
        if self.current_spawn_timer >= self.spawn_timer:
            # create an enemy
            self.current_spawn_timer -= self.spawn_timer
            if self.created_enemies < self.max_enemies:
                self.created_enemies += 1
                self._create_enemy()

class ServerStateObject():
    def __init__(self):
        self.object_name = ''
        self.id = None
        self.eventManager = None
        self.state_changed = False

    def state_has_changed(self):
        if self.state_changed:
            self.state_changed = False
            return True
        else:
            return False

    def set_id(self):
        '''sets the id for this object'''
        self.id = id(self)

    def get_id(self):
        return self.id
        
    def update(self, delta_time):
        pass

class CharacterState(ServerStateObject):
    '''
    Represents a character object in the game state
    '''
    def __init__(self, client_id, client_number, collisionGrid, tile_size):
        ServerStateObject.__init__(self)

        self.client_id = client_id
        self.collisionGrid = collisionGrid
        self.tile_size = tile_size
        
        self.state = 'alive'
        self.object_type = 'character'

        self.ai_grid_strength = 0.1
        
        self.life = 100
        self.movement_speed = 3
        self.position = [0, 0]
        self.velocity = [0.0,0.0]
        
        self.position_has_changed = True
        self.state_changed = True

        self.set_id()

    def get_position(self):
        return self.position

    def package_state(self):
        if self.id:
            object_state = {'object_type': self.object_type,
                            'object_id': self.id,
                            'object_position': self.position,
                            'object_velocity': self.velocity,
                            'object_state': self.state}
            return object_state
        else:
            raise RuntimeError(str(self) + ' has no id')

    def _push_position_to_nearest_open_tile(self, left_position, right_position,
                                            top_position, bottom_position,
                                            colliding_grid_position):
        rect_left = left_position
        rect_right = right_position
        rect_top = top_position
        rect_bottom = bottom_position
        rect_top_left = [rect_left, rect_top] 
        
        tile_left = (colliding_grid_position[0] * self.tile_size) + 1
        tile_right = tile_left + (self.tile_size - 1)
        tile_top = (colliding_grid_position[1] * self.tile_size) + 1
        tile_bottom = tile_top + (self.tile_size - 1)
        
        top_displacement = (tile_top - rect_bottom) - 2
        bottom_displacement = tile_bottom - rect_top
        left_displacement = (tile_left - rect_right) - 2
        right_displacement = tile_right - rect_left

        squared_top_displacement = {'name': 'squared_top_displacement',
                                    'value': top_displacement ** 2}
        squared_bottom_displacement = {'name': 'squared_bottom_displacement',
                                       'value': bottom_displacement ** 2}
        squared_left_displacement = {'name': 'squared_left_displacement',
                                     'value': left_displacement ** 2}
        squared_right_displacement = {'name': 'squared_right_displacement',
                                      'value': right_displacement ** 2}
        #print squared_top_displacement, squared_bottom_displacement, squared_left_displacement, squared_right_displacement

        displacements = []
        displacements.extend([squared_left_displacement,
                              squared_right_displacement,
                              squared_top_displacement,
                              squared_bottom_displacement])

        # Sorting all the displacements to find the smallest one
        sorted_displacements = []
        # for all our unsorted displacements
        for d in displacements:
            # go through all the sorted displacements

            if len(sorted_displacements) == 0:
                sorted_displacements.append(d)
            else:
                for list_index in range(0, (len(sorted_displacements) + 1)):

                    try:
                        # if the unsorted one is greater than the current sorted one
                        if d['value'] > sorted_displacements[list_index]['value']:
                            if len(sorted_displacements) < (list_index - 1):
                                sorted_displacements.append(d)
                                break
                            else:
                                pass
                        else:
                            # if its less
                            sorted_displacements.insert(list_index, d)
                            break
                            
                    except IndexError:
                        sorted_displacements.append(d)

        smallest_displacement = sorted_displacements[0]

        if smallest_displacement['name'] == 'squared_top_displacement':
            rect_top_left[1] += top_displacement
        elif smallest_displacement['name'] == 'squared_bottom_displacement':
            rect_top_left[1] += bottom_displacement
        elif smallest_displacement['name'] == 'squared_left_displacement':
            rect_top_left[0] += left_displacement
        elif smallest_displacement['name'] == 'squared_right_displacement':
            rect_top_left[0] += right_displacement
       
        return rect_top_left

    def move(self, keyboard_input):
        # move in given direction
        if keyboard_input == 'UP':
            self.position[1] -= self.movement_speed
        elif keyboard_input == 'DOWN':
            self.position[1] += self.movement_speed
        elif keyboard_input == 'LEFT':
            self.position[0] -= self.movement_speed
        elif keyboard_input == 'RIGHT':
            self.position[0] += self.movement_speed

        # diagonal movement
        elif keyboard_input == 'LEFTUP':
            self.position[0] -= (self.movement_speed * .707)
            self.position[1] -= (self.movement_speed * .707)
        elif keyboard_input == 'RIGHTUP':
            self.position[0] += (self.movement_speed * .707)
            self.position[1] -= (self.movement_speed * .707)
        elif keyboard_input == 'LEFTDOWN':
            self.position[0] -= (self.movement_speed * .707)
            self.position[1] += (self.movement_speed * .707)
        elif keyboard_input == 'RIGHTDOWN':
            self.position[0] += (self.movement_speed * .707)
            self.position[1] += (self.movement_speed * .707)
        # pixel position
        self.position = [self.position[0], self.position[1]]

        ##### COLLISIONS WITH WALLS #####
        # pixel positions
        left_position = self.position[0]
        right_position = self.position[0] + (self.tile_size - 1)
        top_position = self.position[1]
        bottom_position = self.position[1] + (self.tile_size - 1)

        top_left_position = [left_position, top_position]
        top_right_position = [right_position, top_position]
        bottom_left_position = [left_position, bottom_position]
        bottom_right_position = [right_position, bottom_position]
        # grid positions

        top_left_grid_position = mapgrid.convert_position_to_grid_position(top_left_position, self.tile_size)
        top_right_grid_position = mapgrid.convert_position_to_grid_position(top_right_position, self.tile_size)
        bottom_left_grid_position = mapgrid.convert_position_to_grid_position(bottom_left_position, self.tile_size)
        bottom_right_grid_position = mapgrid.convert_position_to_grid_position(bottom_right_position, self.tile_size)

        if self.collisionGrid.is_tile_open(top_left_grid_position) == False:
            self.position = self._push_position_to_nearest_open_tile(left_position,
                                                                     right_position,
                                                                     top_position,
                                                                     bottom_position,
                                                                     top_left_grid_position)
        if self.collisionGrid.is_tile_open(top_right_grid_position) == False:
            self.position = self._push_position_to_nearest_open_tile(left_position,
                                                                     right_position,
                                                                     top_position,
                                                                     bottom_position,
                                                                     top_right_grid_position)
        if self.collisionGrid.is_tile_open(bottom_left_grid_position) == False:
            self.position = self._push_position_to_nearest_open_tile(left_position,
                                                                     right_position,
                                                                     top_position,
                                                                     bottom_position,
                                                                     bottom_left_grid_position)
        if self.collisionGrid.is_tile_open(bottom_right_grid_position) == False:
            self.position = self._push_position_to_nearest_open_tile(left_position,
                                                                     right_position,
                                                                     top_position,
                                                                     bottom_position,
                                                                     bottom_right_grid_position)



            
        self.state_changed = True

        # HOW IT WILL WORK
        # check if four corners are colliding
        # for all grid positions that the colliding corners are in
        # find the closest wall to push the cube out to
        ##### get positions of walls,
        ##### see which wall has the smallest distance to travel
        # push the character out to that wall

    def update(self):
        # so the server knows if this object needs something
        command_request = None
        
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        return command_request

class EnemyState(ServerStateObject):
    def __init__(self, collisionGrid, aiGrid, position, tile_size):
        ServerStateObject.__init__(self)

        self.collisionGrid = collisionGrid
        self.aiGrid = aiGrid
        self.position = [position[0], position[1]]
        self.tile_size = tile_size
        self.state = 'alive'
        self.object_type = 'enemy'
        self.tile_size = tile_size

        self.center_grid_position = self.get_center_grid_position()
        self.speed = 0.3
        self.velocity = [0.0,0.0]
        self.attack_timer = 300
        self.base_attack_damage = 1
        self.random_roaming_chance = 0.0001
        
        self.target_position = None
        self.roaming_target_position = None
        self.previous_target_position = None
        self.state_changed = True

        self.set_id()
        
        print 'New enemy... id: ' + str(self.id)

    def get_center_grid_position(self):
        center_position = [self.position[0] + (self.tile_size/2),
                           self.position[1] + (self.tile_size/2)]
        
        grid_position = mapgrid.convert_position_to_grid_position(self.position, self.tile_size)
        center_grid_position = mapgrid.convert_position_to_grid_position(center_position, self.tile_size)
        return center_grid_position
    
    def package_state(self):
        if self.id:
            object_state = {'object_type': self.object_type,
                            'object_id': self.id,
                            'object_position': self.position,
                            'object_velocity': self.velocity,
                            'object_state': self.state}
            return object_state
        else:
            raise RuntimeError(str(self) + ' has no id')

    def _move(self, destination_position):
        if destination_position:
            # set a vector for the target
            vector_target_position = mapgrid.Vector(destination_position[0], destination_position[1])
            # set a vector for our position
            vector_position = mapgrid.Vector(self.position[0], self.position[1])
            # subtract the vectors to find total displacement
            displacement_to_target = vector_target_position - vector_position
            # normalize to find direction to move
            velocity = displacement_to_target.normalize()
            # set that as our velocity
            self.velocity = [velocity[0], velocity[1]]
            # move the position
            if displacement_to_target[0] ** 2 < self.speed ** 2:
                self.position[0] += displacement_to_target[0]
            else:
                self.position[0] += (self.velocity[0] * self.speed)

            if displacement_to_target[1] ** 2 < self.speed ** 2:
                self.position[1] += displacement_to_target[1]
            else:
                self.position[1] += (self.velocity[1] * self.speed)

    def _random_roaming_chance(self):
        '''Returns true if we are going to randomly roam'''
        seed = random.random()
        if seed < self.random_roaming_chance:
            return True
        
        
    def get_target_position(self):
        # get the center instead of the topleft
        center_grid_position = self.get_center_grid_position()
        if center_grid_position:
            target_grid_position = self.aiGrid.get_target_grid_position(center_grid_position)
            return target_grid_position
        else:
            raise RuntimeError('No center_grid_position ' + str(center_grid_position))

    def _determine_state(self):
        '''decides which state we are at'''
        
        if self.state in ['roaming']:
            # if were not at our roaming destination
            if self.roaming_target_position != self.position:
                # we still need to keep roaming to get to our destination
                return 'roaming' # we are roaming
            else:  
                # we're done roaming
                self.roaming_target_position = None
                # now moving
                self.state_changed = True
                self.state = 'alive'
            

        # if were not roaming
        # check if we can attack
        if self.target_position:
            # store our previous target
            self.previous_target_position = self.target_position

        # get new target
        self.target_grid_position = self.get_target_position()

        if self._random_roaming_chance():
            self.state = 'roaming'

        # if we have a position to move to
        if self.target_grid_position and self.state != 'roaming':
            target_value = self.aiGrid.get_position_value(self.target_grid_position)
            # if the target is attackable
            if target_value == 1:
                # we are attacking
                return 'attacking'
            else:
                return 'moving'
            
        # if we have nowhere to move to or noone to attack
        else:
            self.state_changed = True

            # pick a random direction, if its open, move to it.
            center_grid_position = self.get_center_grid_position()
            x = center_grid_position[0]
            y = center_grid_position[1]
            direction = self.aiGrid.get_random_direction()
            
            if direction == 'right':
                if self.collisionGrid.is_tile_open([x + 1, y]):
                    self.roaming_target_position = mapgrid.convert_grid_position_to_position([x + 1, y], self.tile_size)
                    return 'roaming'
                else:
                    return 'alive'
                    
            elif direction == 'up':
                if self.collisionGrid.is_tile_open([x, y - 1]):
                    self.roaming_target_position = mapgrid.convert_grid_position_to_position([x, y - 1], self.tile_size)
                    return 'roaming'
                else:
                    return 'alive'
                    
            elif direction == 'left':
                if self.collisionGrid.is_tile_open([x - 1, y]):
                    self.roaming_target_position = mapgrid.convert_grid_position_to_position([x - 1, y], self.tile_size)
                    return 'roaming'
                else:
                    return 'alive'
                   
            elif direction == 'down':
                if self.collisionGrid.is_tile_open([x, y + 1]):
                    self.roaming_target_position = mapgrid.convert_grid_position_to_position([x, y + 1], self.tile_size)
                    return 'roaming'
                else:
                    return 'alive'


    def _get_attack_damage(self):
        '''logic to determine how much damage an attack will do goes here'''
        return self.base_attack_damage
        
    def update(self):

        # so the server knows if this object needs something
        command_request = {'request': None}

        # how it will work
        self.state = self._determine_state()
        # get which state we are currently at
        # react to the state

                

        if self.state == 'attacking':
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_timer += 60
                self.state == 'alive'
                self.state_changed = True
                command_request['request'] = 'attack request'
                command_request['damage'] = self._get_attack_damage()

            self._move(self.previous_target_position)
        
        elif self.state == 'moving':
            if self.target_grid_position:
                # get position of target
                self.target_position = mapgrid.convert_grid_position_to_position(self.target_grid_position, self.tile_size)
                self._move(self.target_position)

        elif self.state == 'roaming':
            if self.roaming_target_position:
                self._move(self.roaming_target_position)
            else:
                raise RuntimeError('No roaming target position: ' + str(self.roaming_target_position))
                
        return command_request

class WallState(ServerStateObject):
    '''
    represents a wall object in the game state
    '''
    def __init__(self, collisionGrid, aiGrid, grid_position):
        ServerStateObject.__init__(self)

        self.grid_position = grid_position
        self.state = 'alive'
        self.object_type = 'wall'

        self.health = 10

        self.ai_grid_strength = 1
        self.max_generations = 20
        self.starting_generation = 1

        self.velocity = [0.0,0.0]
        self.state_changed = True

        self.ai_children_positions = []

        self.collisionGrid = collisionGrid
        self.aiGrid = aiGrid
        self.set_id()
        self._spawn()

    def _spawn(self):
        ''' updates the collision grid and the ai grid'''
        
        self.collisionGrid.close_tile(self.grid_position)
        self.aiGrid.add_source_to_grid(self.grid_position,
                                       self.ai_grid_strength,
                                       self.max_generations,
                                       self.starting_generation,
                                       self)

    def get_grid_position(self):
        return self.grid_position

    def add_ai_child_position(self, child_position):
        self.ai_children_positions.append(child_position)

    def _remove_ai_children_positions(self):
        for p in self.ai_children_positions:
            self.aiGrid.remove_child(self, p)
        self.ai_children_positions = []

    def package_state(self):
        if self.id:
            object_state = {'object_type': self.object_type,
                            'object_id': self.id,
                            'object_position': self.grid_position,
                            'object_velocity': self.velocity,
                            'object_state': self.state}
            # if we are dead
            if self.state == 'dead':
                # we can now request removal from the game because we told the clients we are dead
                self.state = 'pending removal'
                
            return object_state
        else:
            raise RuntimeError(str(self) + ' has no id')

    def destroy_wall(self):
        '''destroy this objects influence on the game world'''

        # remove the influence on the ai grid
        self._remove_ai_children_positions()
        # remove the influence on the collision grid
        self.collisionGrid.open_tile(self.grid_position)
        # change our state
        self.state = 'dead'
        self.state_changed = True
        print 'Wall destroyed'

    def get_attacked(self, attack_damage):
        self.health -= attack_damage
        if self.health <= 0:
            self.destroy_wall()

    def update(self):
        command_request = {'request': None}
        # if we're waiting to be removed from the game
        if self.state == 'pending removal':
            # request to be removed
            command_request['request'] = 'removal request'

        return command_request

class ProjectileState(ServerStateObject):
    '''represents a projectile in the server state'''
    def __init__(self, collisionGrid, spawn_position, destination_position):
        ServerStateObject.__init__(self)

        self.state = 'alive'
        self.object_type = 'projectile'
        self.collisionGrid = collisionGrid

        self.position = [spawn_position[0], spawn_position[1]]
        self._set_velocity(destination_position)
        self.speed = 6
        
        self.set_id()
        
        self.state_changed = True

        print 'New projectile... id: ' + str(self.id)

    def package_state(self):
        if self.id:
            object_state = {'object_type': self.object_type,
                            'object_id': self.id,
                            'object_position': self.position,
                            'object_velocity': self.velocity,
                            'object_state': self.state}
            # if we are dead
            if self.state == 'dead':
                # we can now request removal from the game because we told the clients we are dead
                self.state = 'pending removal'
                
            return object_state
        else:
            raise RuntimeError(str(self) + ' has no id')

    def _set_velocity(self, destination_position):
        if destination_position:
            # set a vector for the target
            vector_target_position = mapgrid.Vector(destination_position[0], destination_position[1])
            # set a vector for our position
            vector_position = mapgrid.Vector(self.position[0], self.position[1])
            # subtract the vectors to find total displacement
            displacement_to_target = vector_target_position - vector_position
            # normalize to find direction to move
            velocity = displacement_to_target.normalize()
            # set that as our velocity
            self.velocity = [velocity[0], velocity[1]]

    def update(self):
        
        self.position[0] += (self.velocity[0] * self.speed)
        self.position[1] += (self.velocity[1] * self.speed)

class ClientState(ServerStateObject):
    '''
    Holds all of the info for each client
    that is connected to the game
    '''
    def __init__(self, client_number, client_ip):
        ServerStateObject.__init__(self)

        self.state = 'alive'
        self.object_type = 'client'

        self.client_number = client_number
        self.client_ip = client_ip

        self.character_id = None

        self.set_id()

    def set_character_id(self, character_id):
        self.character_id = character_id

class ServerView():
    '''
    Controlls game state objects
    such as character, projectile etc...
    '''
    def __init__(self, eventManager, object_registry):
        self.object_registry = object_registry
        self.eventManager = eventManager
        self.eventManager.add_listener(self)

        self.map_dimensions = [25, 20]
        self.tile_size = 32

        self.clients = {}
        self.characters = {}
        self.enemies = {}
        self.walls = {}
        self.projectiles = {}
        self.collisionGrid = mapgrid.CollisionGrid(self.map_dimensions)
        self.aiGrid = mapgrid.AIGrid(self.map_dimensions)

        self.enemyGenerator = EnemyGenerator(self.eventManager)

    def _process_user_keyboard_input_event(self, event):
        # get client number
        client_number = event.client_number
        # get client object
        client = self.clients[client_number]
        # get client's charactr object
        client_character = self.characters[client.character_id]
        # tell character to move
        client_character.move(event.keyboard_input)

    def _process_add_enemy_to_game_request_event(self, event):
        '''
        when the enemy generator wants to spawn an enemy
        '''
        enemyState = EnemyState(self.collisionGrid, self.aiGrid,
                                event.spawn_position, self.tile_size)
        self.enemies[enemyState.id] = enemyState

    def _process_enemy_attack_request(self, enemy, attack_damage):
        enemy_center = enemy.get_center_grid_position()
        for wall_id in self.walls:
            wall = self.walls[wall_id]
            wall_center = self.walls[wall_id].get_grid_position()
            x = wall_center[0]
            y = wall_center[1]
            if enemy_center == [x - 1, y - 1]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x, y - 1]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x + 1, y - 1]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x - 1, y]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x, y]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x + 1, y]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x - 1, y + 1]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x, y + 1]:
                wall.get_attacked(attack_damage)
            elif enemy_center == [x + 1, y + 1]:
                wall.get_attacked(attack_damage)

    def _process_place_wall_request_event(self, event):
        '''when the user wants to place a wall'''
        if self.collisionGrid.is_tile_open(event.grid_position):
            # add a wall to the game
            wall = WallState(self.collisionGrid, self.aiGrid, event.grid_position)
            self.walls[wall.get_id()] = wall

    def _process_shoot_projectile_request_event(self, event):
        '''when the user wants to shoot a projectile'''
        client_number = event.client_number
        client = self.clients[client_number]
        character = self.characters[client.character_id]
        character_position = character.get_position()
        
        projectile = ProjectileState(self.collisionGrid, character_position, event.destination_position)
        self.projectiles[projectile.get_id()] = projectile

    def _add_client_to_game(self, client_number, client_ip):
        clientState = ClientState(client_number, client_ip)
        self.clients[client_number] = clientState
        self._add_character_to_game(clientState.id, client_number)

    def _add_character_to_game(self, client_id, client_number):
        characterState = CharacterState(client_id, client_number, self.collisionGrid, self.tile_size)
        # add the character to our characters group
        self.characters[characterState.id] = characterState
        # let the client know it's character id
        self.clients[client_number].set_character_id(characterState.id)
        
    def _prepare_full_state(self):
        ''' sends full state regardless of if the state has changed '''
        object_states = []
        default_state = object_state = {'object_type': 'default',
                                        'object_id': 000000,
                                        'object_position': [0.0, 0.0],
                                        'object_velocity': [0.0, 0.0],
                                        'object_state': 'default'}
        
        object_states.append(default_state)
        
        for object_id in self.characters:
            current_object = self.characters[object_id]
            if current_object.state == 'pending removal':
                raise RuntimeError('Object state: ' + str(object_state))
            
            object_state = current_object.package_state()
            object_states.append(object_state)
            if not object_state:
                raise RuntimeError('Object state: ' + str(object_state))
            
        for object_id in self.enemies:
            current_object = self.enemies[object_id]
            if current_object.state == 'pending removal':
                raise RuntimeError('Object state: ' + str(object_state))
            
            object_state = current_object.package_state()
            object_states.append(object_state)
            if not object_state:
                raise RuntimeError('Object state: ' + str(object_state))
            
        for object_id in self.walls:
            current_object = self.walls[object_id]
            if current_object.state == 'pending removal':
                raise RuntimeError('Object state: ' + str(object_state))
            
            object_state = current_object.package_state()
            object_states.append(object_state)
            if not object_state:
                raise RuntimeError('Object state: ' + str(object_state))

        for object_id in self.projectiles:
            current_object = self.projectiles[object_id]
            if current_object.state == 'pending removal':
                raise RuntimeError('Object state: ' + str(object_state))
            
            object_state = current_object.package_state()
            object_states.append(object_state)
            if not object_state:
                raise RuntimeError('Object state: ' + str(object_state))
                
        event = events.CompleteGameStateEvent(object_states)
        self.eventManager.post(event)

    def _prepare_changed_state(self):
        ''' send state of objects that have changed their state '''
        object_states = []
        default_state = object_state = {'object_type': 'default',
                                        'object_id': 000000,
                                        'object_position': [0.0, 0.0],
                                        'object_velocity': [0.0, 0.0],
                                        'object_state': 'default'}
        
        object_states.append(default_state)
        
        for object_id in self.characters:
            current_object = self.characters[object_id]
            if current_object.state_has_changed():
                object_state = current_object.package_state()
                object_states.append(current_object.package_state())
                if not object_state:
                    raise RuntimeError('Object state: ' + str(object_state))

        for object_id in self.enemies:
            current_object = self.enemies[object_id]
            if current_object.state_has_changed():
                object_state = current_object.package_state()
                object_states.append(current_object.package_state())
                if not object_state:
                    raise RuntimeError('Object state: ' + str(object_state))
                
        for object_id in self.walls:
            current_object = self.walls[object_id]
            if current_object.state_has_changed(): 
                object_state = current_object.package_state()
                object_states.append(object_state)
                if not object_state:
                    raise RuntimeError('Object state: ' + str(object_state))

        for object_id in self.projectiles:
            current_object = self.projectiles[object_id]
            if current_object.state_has_changed():
                object_state = current_object.package_state()
                object_states.append(object_state)
                if not object_state:
                    raise RuntimeError('Object state: ' + str(object_state))
                
        event = events.ChangedGameStateEvent(object_states)
        self.eventManager.post(event)

    def _update_objects(self):
        for object_id in self.characters:
            # update the character, will return an optional request
            command_requet = self.characters[object_id].update()
            
        for object_id in self.enemies:
            # update the enemy, will return an optional request
            command_request = self.enemies[object_id].update()
            if command_request['request'] == 'attack request':
                enemy = self.enemies[object_id]
                attack_damage = command_request['damage']
                self._process_enemy_attack_request(enemy, attack_damage)

        wall_ids_to_remove = []
        for object_id in self.walls:
            command_request = self.walls[object_id].update()
            if command_request['request'] == 'removal request':
                wall_ids_to_remove.append(object_id)

        for object_id in self.projectiles:
            command_request = self.projectiles[object_id].update()

        for i in wall_ids_to_remove:
            del self.walls[i]
                
        self.aiGrid.update()
        self.enemyGenerator.update(delta_time = 0.025)

    def notify(self, event):
        if event.name == 'Tick Event':
            # !@$%!@%!# SHOULD SEND CHANGED !%@!^#^!
            self._update_objects()
            self._prepare_changed_state()
            self._prepare_full_state()

        elif event.name == 'New Client Connected Event':
            self._add_client_to_game(event.client_number, event.client_ip)
            self._prepare_full_state()
            
        elif event.name == 'User Keyboard Input Event':
            self._process_user_keyboard_input_event(event)

        elif event.name == 'Place Wall Request Event':
            self._process_place_wall_request_event(event)

        elif event.name == 'Shoot Projectile Request Event':
            self._process_shoot_projectile_request_event(event)

        elif event.name == 'Add Enemy To Game Request Event':
            self._process_add_enemy_to_game_request_event(event)
    

def main():
    object_registry = {}
    eventManager = events.EventManager()
    programClock = ProgramClock(eventManager)
    serverView = ServerView(eventManager, object_registry)
    programClock.run()
    
    serverFactory = serverfactory.ServerFactory(eventManager)
    serverFactory.protocol = serverfactory.ClientConnectionProtocol
    reactor.listenTCP(12345, serverFactory)
    print 'started'
    reactor.run()

if __name__ == '__main__':
    import cProfile
    #cProfile.run('main()')
    main()

    
