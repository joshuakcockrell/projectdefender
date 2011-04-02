import os
import pygame
from pygame.locals import *
from twisted.spread import pb
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.main import installReactor


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
    def __init__(self, character):
        self.name = 'Character Move Event'
        self.character = character

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



class Character():
    '''the character object'''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.positionX = None
        self.positionY = None
        self.position = (self.positionX, self.positionY)
        self.speed = 5
        self.state = 'INACTIVE'

    def _move(self, direction):
        if self.state == 'INACTIVE':
            return
        self.positionX += self.speed
        newEvent = CharacterMoveEvent(self)
        self.eventManager.post(newEvent)

    def _spawn(self, position):
        self.position = position
        self.state = 'ACTIVE'
        newEvent = CharacterSpawnEvent(self)
        self.eventManager.post(newEvent)

    def notify(self, event):
        if isinstance(event, GameStartedEvent):
            self._spawn((100,100))

        elif isinstance(event, CharacterMoveRequest):
            self._move(event.direction)



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

class CopyableCharacter():
    def get_state_to_copy(self):
        dictionary = self.__dict__.copy()
        del d['eventManager']
        dictionary['position'] = id(self.position)
        return dictionary

    def set_copyable_state(self, state_dictionary, registry):
        needed_object_ids = []
        sucess = True
        if not registry.has_key(state_dictionary['position']):
            needed_object_ids.append(state_dictionary['position'])
            sucess = False
        else:
            self.position = registry[state_dictionary['position']]
        return [sucess, needed_object_ids]

MixInClass(Character, CopyableCharacter)


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
        from weakref import WeakKeyDictionary
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



################### stuff from serverneeds.py (aka example1.py)

class CPUSpinnerController():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.running = True

    def run(self):
        while self.running:
            newEvent = TickEvent()
            self.eventManager.post(newEvent)

    def notify(self, event):
        if isinstance(event, ProgramQuitEvent):
            self.running = False

class KeyboardController():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def notify(self, event):
        if isinstance(event, TickEvent):
            #go through the user input
            for event in pygame.event.get():
                newEvent = None
                if event.type == QUIT:
                    newEvent = ProgramQuitEvent()
                elif event.type == KEYDOWN:
                    if event.key in [pygame.K_ESCAPE]:
                        newEvent = ProgramQuitEvent()
                    elif event.key in [pygame.K_UP]:
                        newEvent = CharacterMoveRequestEvent('UP')
                if newEvent:
                    self.eventManager.post(newEvent)


class CharacterSprite(pygame.sprite.Sprite):
    def __init__(self, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.image.load(os.path.join('resources','character.png'))
        self.image.convert()
        self.rect = self.image.get_rect()

        self.move_to = None # position to move to during update

    def update(self):
        #set the position to our new move to
        if self.move_to:
            self.rect.center = self.move_to
            self.move_to = None


class PygameView():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        pygame.init()
        self.screen = pygame.display.set_mode((800, 640))
        pygame.display.set_caption('Dude! if you can see this, its working!!!')
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill((120,235,22))
        self.screen.blit(self.background, (0,0))
        pygame.display.flip()

        self.character_sprites = pygame.sprite.RenderUpdates()

    def show_character(self, character):
        characterSprite = CharacterSprite(self.character_sprites)
        position = character.position
        characterSprite = position

    def move_character(self, character):
        characterSprite = self.get_character_sprite(character)

        position = character.position
        characterSprite.move_to(position)

    def get_character_sprite(self, character):
        for c in self.character_sprites:
            return c

    def notify(self, event):
        if isinstance(event, TickEvent):
            self.screen.blit(self.background, (0,0))
            self.character_sprites.update()

            self.character_sprites.draw(self.screen)

            pygame.display.flip()

        elif isinstance(event, CharacterSpawnEvent):
            self.show_character(event.character)

        elif isinstance(event, CharacterMoveEvent):
            self.move_character(event.character)

            
        
######################################

        
class NetworkServerView(pb.Root):
    ''' Used to send events to the Server'''

    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.pbClientFactory = pb.PBClientFactory()
        self.state = 'PREPARING'
        self.reactor = None
        self.server = None

        self.shared_objects = shared_object_registry

    def attempt_connection(self):
        print 'Attempting connection...'
        self.state = 'CONNECTING'
        if self.reactor:
            self.reactor.stop()
            self.pump_reactor()
        else:
            self.reactor = SelectReactor()
            installReactor(self.reactor)
            connection = self.reactor.connectTCP('localhost', 24100, self.pbClientFactory)
            deferred = self.pbClientFactory.getRootObject()
            deferred.addCallback(self.connected)
            deferred.addErrback(self.connect_failed)
            self.reactor.startRunning()

    def disconnect(self):
        print 'disconnecting...'
        if not self.reactor:
            return
        print 'stopping the reactor...'
        self.reactor.stop()
        self.pump_reactor()
        self.state = 'DISCONNECTING'

    def connected(self, server):
        print '...connected!'
        self.server = server
        self.state = 'CONNECTED'
        newEvent = ServerConnectEvent(server)
        self.eventManager.post(newEvent)

    def connect_failed(self, server):
        print '...Connection failed'
        self.state = 'DISCONNECTED'

    def pump_reactor(self):
        self.reactor.runUntilCurrent()
        self.reactor.doIteration(False)
        
    def notify(self, event):
        if isinstance(event, TickEvent):
            if self.state == 'PREPARING':
                self.attempt_connection()
            elif self.state in ['CONNECTED', 'DISCONNECTING', 'CONNECTING']:
                self.pump_reactor()
            return
                
        if isinstance(event, ProgramQuitEvent):
            self.disconnect()
            return

        if not isinstance(event, pb.Copyable):
            print 'not a copyable event:' + str(event)
            event_name = event.__class__.__name__
            copyable_class_name = 'Copyable' + event_name
            if not copyable_class_name in copyable_events:
                return
            copyableClass = copyable_events[copyable_class_name]
            event = copyableClass(event, self.shared_objects)

        if event.__class__ not in client_to_server_events:
            return

        if self.server:
            print 'client sending', str(event)
            remoteCall = self.server.callRemote('EventOverNetwork', event)

        else:
            print 'cannot send while disconnected:', str(event)


class NetworkServerController(pb.Referenceable):
    '''Recieves events from the Server'''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def remote_RecieveEvent(self, event):
        # the server calls this function to send an event
        print 'Event recieved:', str(event)
        self.eventManager.post(event)
        return True

    def notify(self, event):
        if isinstance(event, ServerConnectEvent):
            event.server.callRemote('ClientConnect', self)

def main():
    print '############################################'
    print '##### Starting Project Defender Client #####'
    print '############################################'
    print 'Loading...'

    eventManager = EventManager()
    shared_object_registry = {}

    keyboardController = KeyboardController(eventManager)
    spinnerController = CPUSpinnerController(eventManager)

    pygameView = PygameView(eventManager)

    serverController = NetworkServerController(eventManager)
    serverView = NetworkServerView(eventManager, shared_object_registry)

    print '...Loading Complete!'
    print 'Running Program...'
    spinnerController.run()
    print '...running complete'

if __name__ == '__main__':
    main()
    pygame.quit()
