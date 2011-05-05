import sys
import math
import time

from twisted.internet import selectreactor
selectreactor.install()
from twisted.internet import reactor

from twisted.spread import pb
from twisted.internet import protocol

from weakref import WeakKeyDictionary


###############################################################################
# EVENTS

class Event():
    '''
    superclass for events
    '''
    def __init__(self):
        self.name = 'Default Event'

class TickEvent(Event):
    '''
    frame rate tick
    '''
    def __init__(self, delta_time):
        self.name = 'Tick Event'
        self.delta_time = delta_time

class ProgramQuitEvent(Event):
    '''
    when we quit the program
    '''
    def __init__(self):
        self.name = 'Program Quit Event'

class CompleteGameStateEvent(Event):
    '''
    Holds the  visual info for every
    object in the game
    '''
    # example of game state list
    # [['OBJECT NAME', id, [position]], object2, object3...
    # [['CHARACTER', 19376408, [300, 300]], ['CHARACTER', 19377248, [300, 300]]]
    def __init__(self, game_state_list):
        self.name = 'Complete Game State Event'
        self.game_state = game_state_list

class MapLoadedEvent(Event):
    '''
    after the map has been created
    '''
    def __init__(self, game_map):
        self.name = 'Map Loaded Event'
        self.game_map = game_map

class GameStartRequestEvent(Event):
    def __init__(self):
        self.name = 'Game Start Request Event'

class GameStartedEvent(Event):
    '''
    the game has started
    '''
    def __init__(self, game):
        self.name = 'Game Started'
        self.game = game

class CharacterMoveRequestEvent(Event):
    '''
    when a character moves in a direction
    '''
    def __init__(self, direction):
        self.name = 'Character Move Request'
        self.direction = direction
        
class CreateProjectileRequestEvent(Event):
    '''
    when the character clicks down to shoot a
    projectile
    '''
    def __init__(self, starting_position, target_position):
        self.name = 'Create Projectile Request Event'
        self.starting_position = starting_position
        self.target_position = target_position

class CharacterSpawnEvent(Event):
    '''
    when the character spawns at a position
    '''
    def __init__(self, character):
        self.name = 'Character Spawn'
        self.character = character

class MouseClickEvent(Event):
    '''
    when a user clicks down on the mouse
    '''
    def __init__(self, clickPosition):
        self.name = 'Mouse Click Event'
        self.position = clickPosition

class ServerConnectEvent(Event):
    def __init__(self, serverReference):
        self.name = 'Server Connect Event'
        self.server = serverReference


class ClientConnectEvent(Event):
    def __init__(self, client):
        self.name = 'Client Connect Event'
        self.client = client


copyable_events = {}

server_to_client_events = []
client_to_server_events = []

def MixInClass(origClass, addClass):
    if addClass not in origClass.__bases__:
        origClass.__bases__ += (addClass,)

def MixInCopyClasses(someClass):
    MixInClass(someClass, pb.Copyable)
    MixInClass(someClass, pb.RemoteCopy)


# mixing in the copy classes here
#client to server
MixInCopyClasses(ProgramQuitEvent)
pb.setUnjellyableForClass(ProgramQuitEvent, ProgramQuitEvent)
client_to_server_events.append(ProgramQuitEvent)

#client to server
MixInCopyClasses(GameStartRequestEvent)
pb.setUnjellyableForClass(GameStartRequestEvent, GameStartRequestEvent)
client_to_server_events.append(GameStartRequestEvent)

#client to server
MixInCopyClasses(CharacterMoveRequestEvent)
pb.setUnjellyableForClass(CharacterMoveRequestEvent, CharacterMoveRequestEvent)
client_to_server_events.append(CharacterMoveRequestEvent)


class CopyableGameStartedEvent(pb.Copyable, pb.RemoteCopy):
    '''server to client only'''
    def __init__(self, event, object_registry):
        self.name = 'Copyable Game Started Event'
        self.game_id = id(event.game)
        object_registry[self.game_id] = event.game

pb.setUnjellyableForClass(CopyableGameStartedEvent, CopyableGameStartedEvent)
server_to_client_events.append(CopyableGameStartedEvent)

class CopyableCompleteGameStateEvent(pb.Copyable, pb.RemoteCopy):
    '''server to client only'''
    def __init__(self, event, object_registry):
        self.name = 'Copyable Complete Game State Event'
        self.game_state = event.game_state

pb.setUnjellyableForClass(CopyableCompleteGameStateEvent, CopyableCompleteGameStateEvent)
server_to_client_events.append(CopyableCompleteGameStateEvent)

class CopyableCharacterMoveRequestEvent(pb.Copyable, pb.RemoteCopy):
    def __init__(self, event, object_registry):
        self.name = 'Copyable Character Move Request Event'
        self.character_id = id(event.character)
        object_registry[self.character_id] = event.character

pb.setUnjellyableForClass(CopyableCharacterMoveRequestEvent, CopyableCharacterMoveRequestEvent)
client_to_server_events.append(CopyableCharacterMoveRequestEvent)

class CopyableCharacterSpawnEvent(pb.Copyable, pb.RemoteCopy):
    def __init__(self, event, object_registry):
        self.name = 'Copyable Character Spawn Event'
        self.character_id = id(event.character)
        object_registry[self.character_id] = event.character

pb.setUnjellyableForClass(CopyableCharacterSpawnEvent, CopyableCharacterSpawnEvent)
server_to_client_events.append(CopyableCharacterSpawnEvent)

class CopyableCreateProjectileRequestEvent(pb.Copyable, pb.RemoteCopy):
    '''
    when the character clicks down to shoot a
    projectile
    '''
    def __init__(self, event, object_registry):
        self.name = 'Copyable Create Projectile Request Event'
        self.starting_position = event.starting_position
        self.target_position = event.target_position

pb.setUnjellyableForClass(CopyableCreateProjectileRequestEvent, CopyableCreateProjectileRequestEvent)
client_to_server_events.append(CopyableCreateProjectileRequestEvent)

copyable_events['CopyableGameStartedEvent'] = CopyableGameStartedEvent
copyable_events['CopyableCompleteGameStateEvent'] = CopyableCompleteGameStateEvent
copyable_events['CopyableCharacterMoveRequestEvent'] = CopyableCharacterMoveRequestEvent
copyable_events['CopyableCharacterSpawnEvent'] = CopyableCharacterSpawnEvent
copyable_events['CopyableCreateProjectileRequestEvent'] = CopyableCreateProjectileRequestEvent

class EventManager():
    '''super class event manager'''
    def __init__(self):
        self.listeners = WeakKeyDictionary()
        self.pending_listeners = WeakKeyDictionary()
        self.event_queue = []

    def process_pending_listeners(self):
        '''
        New listeners are added to the listeners list
        in a seperate loop than the post event fuction
        to avoid changing the list of listeners as we
        are iterating through it
        ( which we do in _process_event_queue() )
        '''
        for listener in self.pending_listeners:
            self.listeners[listener] = True
        self.pending_listeners = WeakKeyDictionary() # empty the list

    def register_listener(self, listener):
        self.pending_listeners[listener] = True

    def register_pre_listener(self, listener):
        '''
        Registers starting listeners
        '''
        self.listeners[listener] = True

    def unregister_listener(self, listener):
        if listener in self.listeners:
            del self.listeners[listener]
    def post(self, event):
        self.event_queue.append(event)
        if isinstance(event, TickEvent):
            self.process_pending_listeners() # update the lister list
            self._process_event_queue()
        else:
            pass
        
    def _process_event_queue(self):
        # goes through all the events and sends them to the listeners
        event_number = 0
        while event_number < len(self.event_queue):
            event = self.event_queue[event_number]
            for listener in self.listeners:
                listener.notify(event)
            event_number += 1
        # empty the queue
        self.event_queue = []
        

class ServerEventManager(EventManager):
    '''subclass of event manager that doesn't wait for a Tick event to start
    processing the event queue (the server doesnt use Tick events)
    '''

    def __init__(self):
        EventManager.__init__(self)
        self._locked = False

    def post(self, event):
        EventManager.post(self, event)
        if not self._locked:
            self._locked = True
            self._process_event_queue()
            self._locked = False
        

###############################################################################
# SERVER NETWORK CONTROLLERS



class FrameRateTicker():
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
        self.eventManager.register_listener(self)
        self.program_time = 0.0
        self.initial_time = time.time()
        self.current_time = self.initial_time
        self.delta_time = 0.01 # not sure why .01
        self.extra_time_accumulator = self.delta_time
        self.FPS = 40
        self.minimum_FPS = 4
        
        self.running = True
        self.run()

    def run(self):

        self.last_time = self.current_time # set last time
        self.current_time = time.time() # get current time
        self.delta_time =  self.current_time - self.last_time # get delta time
        if self.delta_time > (1.0 / self.minimum_FPS):
            self.delta_time = (1.0 / self.minimum_FPS)
        sys.stdout.write('\rdelta time: ' + str(self.delta_time))
        sys.stdout.flush()
            
        self.extra_time_accumulator += self.delta_time
        while self.extra_time_accumulator >= self.delta_time:
            newEvent = TickEvent(self.delta_time)
            self.program_time += self.delta_time
            self.extra_time_accumulator -= self.delta_time
            newEvent = TickEvent(self.delta_time)
            self.eventManager.post(newEvent)

        # call this function again
        if self.running == True:
            reactor.callLater((1.0 / self.FPS), self.run)
        else:
            pass

    def notify(self, event):
        if isinstance(event, ProgramQuitEvent): # if we got a quit program event
            self.running = False
            

class NetworkClientController(pb.Root):
    '''gets events from the network'''
    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventManager
        self.eventManager.register_pre_listener(self)
        self.shared_objects = shared_object_registry

    def remote_ClientConnect(self, client):
        # client calls this function to connect sends self as param
        new_event = ClientConnectEvent(client)
        self.eventManager.post(new_event)

    def remote_EventOverNetwork(self, event):
        # server gets an event
        #print 'Event recieved: ' + str(event.name)
        if event.name == 'Program Quit Event':
            print event.name
        self.eventManager.post(event)
        return True

    def notify(self, event):
        # do nothing when notified
        pass

class NetworkClientView(object):
    '''used to send events to clients'''
    def __init__(self, eventManager, object_registry):
        self.eventManager = eventManager
        self.eventManager.register_pre_listener(self)
        self.clients = []
        self.object_registry = object_registry

    def notify(self, event):

        if event.name == 'Tick Event':
            # ticks dont get sent
            return
        
        if isinstance(event, ClientConnectEvent):
            # if a client wants to connect
            self.clients.append(event.client)
            print 'THE CLIENT'
            print event.client

        testing_event = event
        
        if not isinstance(testing_event, pb.Copyable):
            event_name = testing_event.__class__.__name__
            copyable_class_name = 'Copyable' + event_name
            if copyable_class_name not in copyable_events:
                return
            
            copyable_class = copyable_events[copyable_class_name]
            testing_event = copyable_class(testing_event, self.object_registry)
        else:
            pass
        
        # see if the event is in our list of things we can send          
        if testing_event.__class__ in server_to_client_events:
            for c in self.clients:
                remoteCall = c.callRemote('RecieveEvent', testing_event)
        else:
            pass


###############################################################################
# SERVER GAME STATE OBJECTS

class Collision_Tester():
    '''
    stores the rectangle dimensions for all of the sprites
    and tests for collisions between them
    '''
    def __init__(self):
        self.dimensions = {} # holds all the dimensions

        # [width, height]
        self.character_alive_dimensions = [19, 27]

        self.character_dead_dimensions = [40, 40]

        self.projectile_alive_dimensions = [10, 10]
        self.projectile_dying_dimensions = [10, 10]
        self.projectile_dead_dimensions = [10,10]

        self.dimensions['CHARACTERALIVE'] = self.character_alive_dimensions
        self.dimensions['CHARACTERDEAD'] = self.character_dead_dimensions
        self.dimensions['PROJECTILEALIVE'] = self.projectile_alive_dimensions
        self.dimensions['PROJECTILEDYING'] = self.projectile_dying_dimensions
        self.dimensions['PROJECTILEDEAD'] = self.projectile_dead_dimensions

    def test_for_collision(self,
                           object1_name, object1_topleft_position, object1_state,
                           object2_name, object2_topleft_position, object2_state):
        # put into a string (key) such as: CHARACTERALIVE
        object1_dimensions_key = object1_name + object1_state
        object2_dimensions_key = object2_name + object2_state
        # use the keys to get the dimensions
        # raise error if there is no dimensions of that type

        object1_dimensions = self.dimensions[object1_dimensions_key]
        object2_dimensions = self.dimensions[object2_dimensions_key]

        # setting up positions and values
        object1_left = object1_topleft_position[0] # get the left position
        object1_right = object1_left + object1_dimensions[0] # get the right
        object1_top = object1_topleft_position[1] # get the top position
        object1_bottom = object1_top + object1_dimensions[1] # get the bottom

        object2_left = object2_topleft_position[0] # get the left position
        object2_right = object2_left + object2_dimensions[0] # get the right
        object2_top = object2_topleft_position[1] # get the top position
        object2_bottom = object2_top + object2_dimensions[1] # get the bottom


        # testing for the collision
        if object1_bottom < object2_top:
            return False # no collision
        if object1_top > object2_bottom:
            return False # no collision
        if object1_right < object2_left:
            return False
        if object1_left > object2_right:
            return False

        return True # if it has not returned false already, its a collision
    

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
        return None


class GameStateObject():
    def __init__(self):
        self.object_name = ''
        self.id = None
        self.eventManager = None
        
    def update(self, delta_time):
        pass


class CharacterState(GameStateObject):
    '''Game State object that holds Character Logic
    (not visuals or user input)
    '''
    def __init__(self, eventManager):
        GameStateObject.__init__(self)

        self.position_has_changed = False

        self.state = 'ALIVE'
        self.object_type = 'CHARACTER'
        self.id = None
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.life = 100

        self.movement_speed = 5
        self.positionX = 300
        self.positionY = 300
        self.position = [self.positionX, self.positionY]

        self.position_has_changed = True
        self.state_changed = True
        
    def set_id(self, new_id):
        self.id = new_id

    def state_has_changed(self):
        #checks if the velocity has changed for package_info
        if self.position_has_changed == True:
            self.position_has_changed = False
            return True
        # check if the state has changed for package info
        elif self.state_changed == True:
            self.state_changed = False
            return True
        else:
            return False

    def get_hit(self, damage):
        self.life -= damage
        if self.life <= 0:
            self.state = 'DEAD'
            self.state_changed = True

    def package_info(self):
        # send info to the _send_complete_game_state function
        # to be sent to the clients as an update
        if self.id: # if we have an id already
            # example: [object type, id, [position], [velocity], state]
            return [self.object_type, self.id, self.position, None, self.state]
        
    def move(self, direction):
        #print 'the character is moving in ' + str(direction)
        #if self.state == 'ALIVE':

        # move in given direction
        if direction == 'UP':
            self.positionY -= self.movement_speed
        elif direction == 'DOWN':
            self.positionY += self.movement_speed
        elif direction == 'LEFT':
            self.positionX -= self.movement_speed
        elif direction == 'RIGHT':
            self.positionX += self.movement_speed

        # diagonal movement
        elif direction == 'LEFTUP':
            self.positionX -= (self.movement_speed * .707)
            self.positionY -= (self.movement_speed * .707)
        elif direction == 'RIGHTUP':
            self.positionX += (self.movement_speed * .707)
            self.positionY -= (self.movement_speed * .707)
        elif direction == 'LEFTDOWN':
            self.positionX -= (self.movement_speed * .707)
            self.positionY += (self.movement_speed * .707)
        elif direction == 'RIGHTDOWN':
            self.positionX += (self.movement_speed * .707)
            self.positionY += (self.movement_speed * .707)

        self.position = [self.positionX, self.positionY]
        self.position_has_changed = True

    def notify(self, event):
        pass

    def update(self, delta_time):
        pass

class ProjectileState(GameStateObject):
    '''
    Game State object that holds projectile Logic
    (not visuals or user input)
    '''
    def __init__(self, eventManager, starting_position, target_position, emitter_id):
        GameStateObject.__init__(self)

        self.velocity_has_changed = False
        self.state = 'ALIVE'
        self.object_type = 'PROJECTILE'
        self.id = None
        self.emitter_id = emitter_id
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.movement_speed = 50
        self.positionX = starting_position[0]
        self.positionY = starting_position[1]
        self.position = [self.positionX, self.positionY]

        self.damage = 25
        
        self.target_positionX = target_position[0]
        self.target_positionY = target_position[1]
        self.target_position = [self.target_positionX, self.target_positionY]

        self.velocity = None # direction with magnitude
        self.direction = None # just direction vector
        self.velocity = self.get_velocity()
        
        self.velocity_has_changed = True
        self.state_changed = True

        self.DURATION_OF_DYING_STATE = 60 # time between alive and dead states
        self.duration_of_dying_state = self.DURATION_OF_DYING_STATE

    def set_id(self, new_id):
        self.id = new_id

    def state_has_changed(self):
        # check if the velocity has changed for package_info
        if self.velocity_has_changed == True:
            self.velocity_has_changed = False
            return True
        # check if the state has changed for package info
        elif self.state_changed == True:
            self.state_changed = False
            return True
        else:
            return False
            
    def package_info(self):
        # send info to the _send_complete_game_state function
        # to be sent to the clients as an update
        if self.id: # if we have an id already
            return [self.object_type, self.id, self.position, self.velocity, self.state] # send stuff

    def get_velocity(self):
        if self.target_position: # if the square has a target
            position = Vector(self.positionX, self.positionY) # create a vector from center x,y value
            target = Vector(self.target_positionX, self.target_positionY) # and one from the target x,y
            self.distance = target - position # get total distance between target and position

            self.direction = self.distance.normalize() # normalize so its constant in all directions
            velocityX = self.direction[0] * self.movement_speed
            velocityY = self.direction[1] * self.movement_speed
            self.velocity = [velocityX, velocityY]
            return self.velocity

    def _is_dead(self):
        if self.state != 'DEAD':
            self.state = 'DEAD'
            self.velocity = [0,0]
            self.velocity_has_changed = True
            self.state_changed = True

    def _is_dying(self):
        if self.state == 'ALIVE':
            self.state = 'DYING'
            self.state_changed = True
            self.duration_of_dying_state = self.DURATION_OF_DYING_STATE

    def notify(self, event):
        pass

    def update(self, delta_time):
        # delta time is used to determine
        # how far to advance the object state
        #print self.positionX
        #print delta_time
        # if were dying
        if self.state == 'DYING':
            self.duration_of_dying_state -= 1
            if self.duration_of_dying_state <= 0:
                self._is_dead()
        # if alive. we can check if we need to die
        if self.state == 'ALIVE':
            if self.positionX < 0:
                self._is_dying()
            if self.positionX > 400:
                self._is_dying()
            if self.positionY < 0:
                self._is_dying()
            if self.positionY > 640:
                self._is_dying()

        if self.state in ['ALIVE', 'DYING']:
            self.positionX += (self.velocity[0] * delta_time) # calculate speed from direction to move and speed constant
            self.positionY += (self.velocity[1] * delta_time)
            self.position = (round(self.positionX),round(self.positionY)) # apply values to object position

class Game():
    '''
    Controlls game state objects
    such as character, projectile etc...
    '''
    def __init__(self, eventManager, object_registry):
        self.eventManager = eventManager
        self.eventManager.register_pre_listener(self)

        self.state = 'PREPARING'

        self.collision_tester = Collision_Tester()

        #self.players = [Player(eventManager)]
        self.object_ids = [] # holds the ids for all the objects
        self.object_registry = object_registry #holds the objects and their id
        self.characters = []
        self.projectiles = []
        self.all_objects = []
                
    def start(self):
        print 'Starting Game...'
        #pre game loop loading stuff
        
        self.state = 'RUNNING'
        new_event = GameStartedEvent(self)
        self.eventManager.post(new_event)

    def _update_game_state(self, delta_time):
        ''' updates all the objects in self.all_objects
        it uses delta time to determine how far ahead the objects
        state should advance
        '''
        # update objects
        for o in self.all_objects:
            o.update(delta_time)
                
        # test for collisions
        for c in self.characters:
            for p in self.projectiles:
                # cant hit the character with his own shots!
                if p.emitter_id == c.id:
                    break # move onto new projectile
                else:
                #print p.emitter_id, c.id
                # if they are colliding
                    if self.collision_tester.test_for_collision(c.object_type, c.position, c.state,
                                                                p.object_type, p.position, p.state):
                        c.get_hit(p.damage) # hit the character
    

    def _create_new_character(self):
        #spawn a character
        character = CharacterState(self.eventManager) # create a character
        character_id = id(character) # get the id
        character.set_id(character_id) # set the id

        #add to groups
        self.object_registry[character_id] = character
        self.all_objects.append(character)
        self.characters.append(character)
        self.object_ids.append(character_id)

    def _create_new_projectile(self, starting_position, target_position, emitter_id):
        projectile = ProjectileState(self.eventManager, starting_position, target_position, emitter_id)
        projectile_id = id(projectile)
        projectile.set_id(projectile_id)

        #add to groups
        self.object_registry[projectile_id] = projectile
        self.all_objects.append(projectile)
        self.projectiles.append(projectile)
        self.object_ids.append(projectile_id)

    def _send_complete_game_state(self):
        game_objects_info = []
        for object_id in self.object_ids:
            current_object = self.object_registry[object_id]
            current_object_info = current_object.package_info()
            if current_object.state_has_changed():
                game_objects_info.append(current_object_info)

        if not game_objects_info: # if its none
            pass
        else:
            newEvent = CompleteGameStateEvent(game_objects_info)
            self.eventManager.post(newEvent)
    def notify(self, event):

        if event.name == 'Tick Event':
            #update all the objects
            self._update_game_state(event.delta_time)
            self._send_complete_game_state()
        
        if isinstance(event, GameStartRequestEvent):
            if self.state == 'RUNNING':
                self.start()
                
        if event.name == 'Client Connect Event':
            self._send_complete_game_state()
            self._create_new_character()

        if event.name == 'Copyable Character Move Request Event':
            # get the correct character
            character_to_move = self.object_registry[event.character_id]
            character_to_move.move(event.direction)

        elif event.name == 'Copyable Create Projectile Request Event':
            self._create_new_projectile(event.starting_position, event.target_position, event.emitter_id)
            

def main():
    print '############################################'
    print '##### Starting Project Defender Server #####'
    print '############################################'
    print 'Loading...'
    
    eventManager = ServerEventManager()
    frameRateTicker = FrameRateTicker(eventManager)
    object_registry = {}
    clientController = NetworkClientController(eventManager, object_registry)
    clientView = NetworkClientView(eventManager, object_registry)
    game = Game(eventManager, object_registry)

    
    reactor.listenTCP(24100, pb.PBServerFactory(clientController))

    print '...Loading Complete!'
    print 'Running Program...'
    reactor.run()


if __name__ == '__main__':
    import cProfile
    cProfile.run('main()')
    #main()
