import os
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


server_to_client_events = []
client_to_server_events = []

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
        self.eventQueue.append(event)
        if isinstance(event, TickEvent):
            self._process_event_queue()
        else:
            print event.name

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

class CPUSpineerController():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.running = True

    def run(self):
        while self.running:
            newEvent = TickEvent()
            self.eventManager.post(newEvent)

    def notify(self, event):
        if isinstance(event, QuitEvent):
            self.running = False


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

            self.character_sprites.draw(screen)

            pygame.display.flip()

        elif isinstance(event, CharacterSpawnEvent):
            self.show_character(event.character)

        elif isinstance(event, CharacterMoveEvent):
            self.move_character(event.character)

        

            
        
        
        


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

class CopyableCharacterSpawnEvent(pb.Copyable, pb.RemoteCopy):
    def __init__(self, event, registry):
        self.name = 'Copyable Character Spawn Event'
        self.character_id = id(event.character)
        registry[self.character_id] = event.character

pb.setUnjellyableForClass(CopyableCharacterSpawnEvent, CopyableCharacterSpawnEvent)
server_to_client_events.append(CopyableCharacterSpawnEvent)
        
######################################

        
class NetworkServerView(pb.Root):

    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.pbClientFactory = pb.PBClientFactory()
        self.state = 'PREPARING'
        self.reactor = None
        self.server = None

        self.shared_objects = shared_object_registry

    def attempt_connection(self):
        print 'Attempting connection'
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
                event_name = event.__class__.__name__
                copyable_class_name = 'Copyable' + event_name
                if not hasattr(network, copyable_class_name):
                    return
                copyableClass = getattr(network, copyable_class_name)
                event = copyableClass(event, self.shared_objects)

            if event.__class__ not in client_to_server_events:
                return

            if self.server:
                print 'client sending', str(event)
                remoteCall = self.server.callRemote('EventOverNetwork', event)

            else:
                print 'cannot send while disconnected:', str(event)


class NetworkServerController(pb.Referenceable):
    '''events are recieved from the network through this controller'''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def remote_ServerEvent(self, event):
        print 'dude!!! whhoooeeee we got an event:', str(event)
        self.eventManager.post(event)
        return True

    def notify(self, event):
        if isinstance(event, ServerConnectEvent):
            event.server.callRemote('ClientConnect', self)

class PhonyEventManager(EventManager):
    def post(self, event):
        pass

class PhonyModel(object):
    ''' model used to store the local state and to interact with
    the local Event Manager
    '''
    def __init__(self, eventManager, shared_object_registry):
        self.shared_objects = shared_object_registry
        self.game = None #HAHAHAHA NO GHAME FOR YOU! UP YOURS!
        self.server = None
        self.phonyEventManager = PhonyEventManager()
        self.realEventManager = eventManager
        self.realEventManager.register_listener(self)

    def StateReturned(self, response):
        if response[0] == False:
            print 'response[0] is false, uh, dude...'
            return None
        object_ids = response[0]
        object_dictionary = response[1]
        the_object = self.shared_objects[object_id]

        retval = the_object.setCopyableState(object_dictionary, self.shared_objects)
        if retval[0] == True:
            return the_object
        for remaining_object_id in retval[1]:
            remoteResponse = self.server.callRemote('GetObjectState', remaining_object_id)
            remoteResponse.addCallback(self.StateReturned)

        retval = obj.setCopyableState(object_dictionary, self.shared_objects)
        if retval[0] == False:
            print 'ummm why is that wierd? i dont know, but it is.'
            return None

        return the_object

    def notify(self, event):
        if isinstance(event, ServerConnectEvent):
            self.server = event.server
        elif isinstance(event, CopyableGameStartedEvent):
            game_id = event.game_id
            if not self.game:
                self.game = Game(self.phonyEventManager)
                self.shared_objects[game_id] = self.game
                
            print 'sending the thing to the real em'
            newEvent = GameStartedEvent(self.game)
            self.realEventManager.post(newEvent)


        if isinstance(event, CopyableCharacterSpawnEvent):
            character_id = event.character_id
            if self.shared_objects.has_key(character_id):
                character = self.shared_objects[character_id]
                newEvent = CharacterPlaceEvent(character)
                self.realEventManager.post(event)
            else:
                character = self.game.players[0].characters[0]
                self.shared_objects[character_id] = character
                remoteResponse = self.server.callRemote('GetObjectState', character_id)
                remoteResponse.addCallback(self.StateReturned)
                remoteResponse.addCallback(self.CharacterSpawnCallback)

        if isinstance(event, CopyableCharacterMoveEvent):
            character_id = event.character_id
            if self.shared_objects.has_key(character_id):
                character = self.shared_objects[character_id]
            else:
                character = self.game.players[0].characters[0]
                self.shared_objects[character_id] = character
            remoteResponse = self.server.callRemote('GetObjectState', character_id)
            remoteResponse.addCallback(self.StateReturned)
            remoteResponse.addCallback(self.CharacterMoveRequestCallback)
            

    def CharacterSpawnCallback(self, character):
        newEvent = CharacterSpawnEvent(character)
        self.realEventManager.post(event)

    def CharacterMoveCallback(self, character):
        newEvent = CharacterMoveEvent(character)
        self.realEventManager.post(event)

def main():

    eventManager = EventManager()
    shared_object_registry = {}

    keyboardController = KeyboardController(eventManager)
    spinnerController = CPUSpinnerController(eventManager)

    pygameView = PygameView(eventManager)
    

    phonyModel = PhonyModel(eventManager, shared_object_registry)

    serverController = NetworkServerController(eventManager)
    serverView = NetworkServerView(eventManager, shared_object_registry)

    spinnerController.run()
    print 'running complete'
    print eventManager.event


