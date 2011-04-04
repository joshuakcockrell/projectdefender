from twisted.spread import pb
from twisted.internet import protocol
from twisted.internet import reactor

from weakref import WeakKeyDictionary

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
    def __init__(self):
        self.name = 'Tick Event'

class ProgramQuitEvent(Event):
    '''
    when we quit the program
    '''
    def __init__(self):
        self.name = 'Program Quit Event'

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

class CharacterMoveEvent(Event):
    '''
    when a character moves
    '''
    def __init__(self, character, position):
        self.name = 'Character Move Event'
        self.character = character
        self.position = position

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

##class Character():
##    '''the character object'''
##    def __init__(self, eventManager):
##        self.eventManager = eventManager
##        self.eventManager.register_listener(self)
##
##        self.positionX = None
##        self.positionY = None
##        self.position = (self.positionX, self.positionY)
##        self.speed = 5
##        self.state = 'ACTIVE'
##
##    def _move(self, direction):
##        if self.state == 'INACTIVE':
##            return
##        self.positionX += self.speed
##        newEvent = CharacterMoveEvent(self)
##        self.eventManager.post(newEvent)
##
##    def notify(self, event):
##
##        if isinstance(event, CharacterMoveRequestEvent):
##            self._move(event.direction)
##


copyable_events = {}

server_to_client_events = []
client_to_server_events = []

######################## Stuff from network.py
def MixInClass(origClass, addClass):
    if addClass not in origClass.__bases__:
        origClass.__bases__ += (addClass,)

def MixInCopyClasses(someClass):
    MixInClass(someClass, pb.Copyable)
    MixInClass(someClass, pb.RemoteCopy)

##class CopyableCharacter():
##    def get_state_to_copy(self):
##        dictionary = self.__dict__.copy()
##        del d['eventManager']
##        dictionary['position'] = id(self.position)
##        return dictionary
##
##    def set_copyable_state(self, state_dictionary, registry):
##        needed_object_ids = []
##        sucess = True
##        if not registry.has_key(state_dictionary['position']):
##            needed_object_ids.append(state_dictionary['position'])
##            sucess = False
##        else:
##            self.position = registry[state_dictionary['position']]
##        return [sucess, needed_object_ids]
##
#MixInClass(Character, CopyableCharacter)


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
pb.setUnjellyableForClass(CharacterMoveRequestEvent,CharacterMoveRequestEvent)
client_to_server_events.append(CharacterMoveRequestEvent)

class CopyableGameStartedEvent(pb.Copyable, pb.RemoteCopy):
    '''server to client only'''
    def __init__(self, event, registry):
        self.name = 'Copyable Game Started Event'
        self.game_id = id(event.game)
        registry[self.game_id] = event.game

pb.setUnjellyableForClass(CopyableGameStartedEvent, CopyableGameStartedEvent)
server_to_client_events.append(CopyableGameStartedEvent)

class CopyableCharacterMoveEvent(pb.Copyable, pb.RemoteCopy):
    def __init__(self, event, registry):
        self.position = event.position # position to place character
        self.name = 'Copyable Character Move Event'
        self.character_id = id(event.character)
        registry[self.character_id] = event.character

pb.setUnjellyableForClass(CopyableCharacterMoveEvent, CopyableCharacterMoveEvent)
server_to_client_events.append(CopyableCharacterMoveEvent)

class CopyableCharacterMoveRequestEvent(pb.Copyable, pb.RemoteCopy):
    def __init__(self, event, registry):
        self.name = 'Copyable Character Move Request Event'
        self.character_id = id(event.character)
        registry[self.character_id] = event.character

pb.setUnjellyableForClass(CopyableCharacterMoveRequestEvent, CopyableCharacterMoveRequestEvent)
server_to_client_events.append(CopyableCharacterMoveRequestEvent)

class CopyableCharacterSpawnEvent(pb.Copyable, pb.RemoteCopy):
    def __init__(self, event, registry):
        self.name = 'Copyable Character Spawn Event'
        self.character_id = id(event.character)
        registry[self.character_id] = event.character

pb.setUnjellyableForClass(CopyableCharacterSpawnEvent, CopyableCharacterSpawnEvent)
server_to_client_events.append(CopyableCharacterSpawnEvent)

copyable_events['CopyableGameStartedEvent'] = CopyableGameStartedEvent
copyable_events['CopyableCharacterMoveEvent'] = CopyableCharacterMoveEvent
copyable_events['CopyableCharacterMoveRequestEvent'] = CopyableCharacterMoveRequestEvent
copyable_events['CopyableCharacterSpawnEvent'] = CopyableCharacterSpawnEvent




class EventManager():
    '''super class event manager'''
    def __init__(self):
        self.listeners = WeakKeyDictionary()
        self.event_queue = []

    def register_listener(self, listener):
        self.listeners[listener] = True

    def unregister_listener(self, listener):
        if listener in self.listeners:
            del self.listeners[listener]
    def post(self, event):
        self.event_queue.append(event)
        if isinstance(event, TickEvent):
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
            
class TextLogView(object):
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def notify(self, event):
        if isinstance(event, TickEvent):
            return

        pass
    

class NetworkClientController(pb.Root):
    '''gets events from the network'''
    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.shared_objects = shared_object_registry

    def remote_ClientConnect(self, client):
        # client calls this function to connect sends self as param
        new_event = ClientConnectEvent(client)
        self.eventManager.post(new_event)

    def remote_EventOverNetwork(self, event):
        # server gets an event
        #print 'Event recieved: ' + str(event.name)
        self.eventManager.post(event)
        return True

    def notify(self, event):
        # do nothing when notified
        pass

class NetworkClientView(object):
    '''used to send events to clients'''
    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.clients = []
        self.shared_objects = shared_object_registry

    def notify(self, event):
        if isinstance(event, ClientConnectEvent):
            # if a client wants to connect
            self.clients.append(event.client)

        testing_event = event
        
        if not isinstance(testing_event, pb.Copyable):
            event_name = testing_event.__class__.__name__
            copyable_class_name = 'Copyable' + event_name
            if copyable_class_name not in copyable_events:
                return
            copyable_class = copyable_events[copyable_class_name]
            testing_event = copyable_class(testing_event, self.shared_objects)
        if testing_event.__class__ not in server_to_client_events:
            # not gonna send that
            return
        
        #print 'Sending Event: ' + str(testing_event.name)
        for c in self.clients:
            remoteCall = c.callRemote('RecieveEvent', testing_event)

##class Player():
##    '''A person playing the game'''
##    def __init__(self, eventManager):
##        self.eventManager = eventManager
##
##        self.characters = [Character(eventManager)]

class CharacterState():
    '''Game State object that holds Character Logic
    (not visuals or user input)
    '''
    def __init__(self, eventManager):

        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.movement_speed = 5
        self.positionX = 300
        self.positionY = 300
        self.position = [self.positionX, self.positionY]

    def move(self, direction):
        #print 'the character is moving in ' + str(direction)

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
        newEvent = CharacterMoveEvent(self, self.position)
        self.eventManager.post(newEvent)

    def notify(self, event):
        pass
            
    

class Game():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.state = 'PREPARING'

        #self.players = [Player(eventManager)]

        self.characters = []
        characterState = CharacterState(self.eventManager)
        self.characters.append(characterState)

    def start(self):
        print 'Starting Game...'
        #pre game loop loading stuff

        #spawn a character
        character = CharacterState(self.eventManager)
        self.characters.append(character)
        
        
        self.state = 'RUNNING'
        new_event = GameStartedEvent(self)
        self.eventManager.post(new_event)

    def notify(self, event):
        if isinstance(event, GameStartRequestEvent):
            if self.state == 'RUNNING':
                self.start()

        if isinstance(event, CharacterMoveRequestEvent):
            for c in self.characters:
                c.move(event.direction)


            

def main():
    print '############################################'
    print '##### Starting Project Defender Server #####'
    print '############################################'
    print 'Loading...'
    
    eventManager = ServerEventManager()
    shared_object_registry = {}
    log = TextLogView(eventManager)
    clientController = NetworkClientController(eventManager, shared_object_registry)
    clientView = NetworkClientView(eventManager, shared_object_registry)
    game = Game(eventManager)

   
    
    reactor.listenTCP(24100, pb.PBServerFactory(clientController))

    print '...Loading Complete!'
    print 'Running Program...'
    reactor.run()


if __name__ == '__main__':
    main()
