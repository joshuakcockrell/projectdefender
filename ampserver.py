# twisted imports
from twisted.internet import reactor

# python imports
import time

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

class ServerStateObject():
    def __init__(self):
        self.object_name = ''
        self.id = None
        self.eventManager = None
        self.state_changed = False

    def state_has_changed(self):
        if self.state_changed == True:
            self.state_changed = False
            return True
        else:
            return False

    def set_id(self, new_id):
        '''
        sets the id for this object,
        this must be done after the object's __init__ method
        has been run
        '''
        self.id = new_id
        
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
        
        self.life = 100
        self.movement_speed = 3
        self.position = [300, 300]
        self.velocity = [0.0,0.0]
        
        self.position_has_changed = True
        self.state_changed = True

    def state_has_changed(self):
        return self.state_changed

    def package_state(self):
        if self.id:
            object_state = {'object_type': self.object_type,
                            'object_id': self.id,
                            'object_position': self.position,
                            'object_velocity': self.velocity,
                            'object_state': self.state}

            return object_state # send stuff

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
        '''
        displacements = [{'name': 'hi', 'value': 3},
                         {'name': 'ye', 'value': 4},
                         {'name': 'no', 'value': 1},
                         {'name': 'ok', 'value': 2},
                         {'name': 'aa', 'value': 9},
                         {'name': 'ba', 'value': 1},
                         {'name': 'ba', 'value': 3}]
        '''
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
            
        '''
        if squared_left_displacement > squared_right_displacement:
            # character is closer to right of tile
            print 'closer to right'
            rect_top_left[0] += right_displacement
        else:
            # character is closer to left of tile
            print 'closer to left'
            rect_top_left[0] += left_displacement

        if squared_top_displacement > squared_bottom_displacement:
            # character is closer to bottom of tile
            print 'closer to bottom'
            rect_top_left[1] += bottom_displacement
        else:
            # character is closer to top of tile
            print 'closer to top'
            rect_top_left[1] += top_displacement
        '''

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



            
        self.position_has_changed = True

        # HOW IT WILL WORK
        # check if four corners are colliding
        # for all grid positions that the colliding corners are in
        # find the closest wall to push the cube out to
        ##### get positions of walls,
        ##### see which wall has the smallest distance to travel
        # push the character out to that wall

    def update(self):
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

class WallState(ServerStateObject):
    '''
    represents a wall object in the game state
    '''
    def __init__(self, grid_position):
        ServerStateObject.__init__(self)

        self.grid_position = grid_position
        self.state = 'alive'
        self.object_type = 'wall'

        self.velocity = [0.0,0.0]      
        self.state_changed = True

    def package_state(self):
        if self.id:
            object_state = {'object_type': self.object_type,
                            'object_id': self.id,
                            'object_position': self.grid_position,
                            'object_velocity': self.velocity,
                            'object_state': self.state}
            return object_state


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
        self.walls = {}
        self.collisionGrid = mapgrid.CollisionGrid(self.map_dimensions)

    def _process_user_keyboard_input_event(self, event):
        # get client number
        client_number = event.client_number
        # get client object
        client = self.clients[client_number]
        # get client's charactr object
        client_character = self.characters[client.character_id]
        # tell character to move
        client_character.move(event.keyboard_input)

    def _process_place_wall_request_event(self, event):
        '''
        when the user wants to place a wall
        '''
        if self.collisionGrid.is_tile_open(event.grid_position):
            # add a wall to the game
            self.collisionGrid.close_tile(event.grid_position)
            wall = WallState(event.grid_position)
            wall_id = id(wall)
            wall.set_id(wall_id)
            self.walls[wall_id] = wall

    def _add_client_to_game(self, client_number, client_ip):
        clientState = ClientState(client_number, client_ip)
        client_id = id(clientState)
        clientState.set_id(client_id)
        self.clients[client_number] = clientState

        self._add_character_to_game(client_id, client_number)

    def _add_character_to_game(self, client_id, client_number):
        characterState = CharacterState(client_id, client_number, self.collisionGrid, self.tile_size)
        character_id = id(characterState)
        characterState.set_id(character_id)
        # add the character to our characters group
        self.characters[character_id] = characterState
        # let the client know it's character id
        self.clients[client_number].set_character_id(character_id)
        self._send_full_state()

    def _send_full_state(self):
        ''' sends full state regardless of if the state has changed '''
        object_states = []
        for object_id in self.characters:
            current_object = self.characters[object_id]
            object_state = current_object.package_state()
            object_states.append(object_state)
        for object_id in self.walls:
            current_object = self.walls[object_id]
            object_state = current_object.package_state()
            object_states.append(object_state)
        event = events.CharacterStatesEvent(object_states)
        self.eventManager.post(event)

    def _send_changed_state(self):
        ''' send state of objects that have changed their state '''
        object_states = []
        for object_id in self.characters:
            current_object = self.characters[object_id]
            if current_object.state_has_changed():
                object_state = current_object.package_state()
                object_states.append(current_object.package_state())
                
        for object_id in self.walls:
            current_object = self.walls[object_id]
            if current_object.state_has_changed(): 
                object_state = current_object.package_state()
                object_states.append(object_state)
        event = events.CharacterStatesEvent(object_states)
        self.eventManager.post(event)

    def _update_objects(self):
        for object_id in self.characters:
            self.characters[object_id].update()

    def notify(self, event):
        if event.name == 'Tick Event':
            self._send_changed_state()
            self._update_objects()

        elif event.name == 'New Client Connected Event':
            self._add_client_to_game(event.client_number, event.client_ip)
            self._send_full_state()
            
        elif event.name == 'User Keyboard Input Event':
            self._process_user_keyboard_input_event(event)

        elif event.name == 'Place Wall Request Event':
            self._process_place_wall_request_event(event)
    


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
    main()
