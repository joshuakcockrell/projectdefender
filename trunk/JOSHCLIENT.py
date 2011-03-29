import os
from twisted.spread import pb
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.main import installReactor


server_to_client_events = []
client_to_server_events = []


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
    if addClass not in orgClass.__bases__:
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
MixInCopyClasses(QuitEvent)
pb.setUnjellyableForClass(QuitEvent, QuitEvent)
client_to_server_events.append(QuitEvent)

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
        registry[self.game_id = event.game]

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

class PhonyEventManager(eventManager):
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
    '''
    game start request
    '''
    def __init__(self):
        self.name = 'Game Start Request'

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
    '''
    when the server has connected
    '''
    def __init__(self, serverReference):
        self.name = 'Server Connect Event'
        self.server = serverReference

class ClientConnectEvent(Event):
    '''
    the server generates this event when a client has connected
    '''
    def __init__(self, client):
        self.name = 'Client Connect Event'
        self.client = client
        


    
class NetworkServerView(pb.Root):
    '''Sends events to the server using this class'''

    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventMangager
        self.eventManager.register_listener(self)

        self.pbClientFactory = pb.PBClientFactory()
        self.state = 'PREPARING'

        self.reactor = None
        self.server = None

        self.shared_objects = shared_object_registry


    def AttemptConnection(self):
        print 'attempting connection'
        self.state = 'CONNECTING'
        if self.reactor:
            self.reactor.stop()
            self.pump_reactor()
        else:
            self.reactor = SelectReactor()
            installReactor(self.reactor)

        connection = self.reactor.connectTCP('localhost', 24100, self.pbClientFactory)

        deferred = self.pbClientFactory.getRootObject()
        deferred.addCallback(self.Connected)
        deferred.addErrback(self.ConnectFailed)
        self.reactor.startRunning()

    def _disconnect(self):
        print 'disconnecting'
        if not self.reactor:
            return
        print 'stopping the server'
        self.reactor.stop()
        self.PumpReactor()
        self.state = 'DISCONNECTING'

    def Connected(self, server):
        print 'Connection Sucessful!'
        self.server = server
        self.state = 'CONNECTED'
        new_event = ServerConnectEvent(server)
        self.eventManager.post(new_event)

    def ConnectFailed(self, server):
        print 'Connection Failed...'
        self.state = 'DISCONNECTED'

    def _pump_reactor(self):
        self.reactor.runUntilCurrent()
        self.reactor.doIteration(False)

    def notify(self, event):
        if isinstance(event, TickEvent):
            if self.state == 'PREPARING':
                self.AttemptConnection()
            elif self.state in ['CONNECTED', 'DISCONNECTING', 'CONNECTING']:
                self._pump_reactor()
            return

        if isinstance(event, QuitEvent):
            self._disconnect()
            return

        new_event = event

        if not isinstance(event, pb.Copyable):
            event_name = event.__class__.__name__
            copyable_class_name = 'Copyable' + event_name
            if not hasattr(network, copyable_class_name):
                return
            copyable_class = getattr(network, copyable_class_name)
            new_event = copyable_class(event, self.shared_objects)

        if new_event.__class__ not in netw
        



















import os
import pygame
from pygame.locals import *
from twisted.spread import pb
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.main import installReactor
from twisted.internet import reactor, protocol
from twisted.protocols import amp



class EventManager():
    '''
    coordinates communication between GameState, Display, and Inputs
    '''
    def __init__(self):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary() # weak dictionary for listeners
        self.eventQueue = []

    def register_listener(self, listener):
        self.listeners[listener] = 1

    def unregister_listener(self, listener):
        if listener in self.listeners:
            del self.listeners[listener] # remove the listener

    def post(self, event):
        if event.name == 'Tick Event':
            pass
        else:
            print event

        for listener in self.listeners:
            listener.notify(event)

#---------------------------------------------------------


class InputController():
    '''
    handles the pygame event queue and generates events which can be sent
    over the network
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def notify(self, event):
        if isinstance(event, TickEvent): # if the event is a clock tick
            # handle pygame events
            for event in pygame.event.get():
                newEvent = None # newly generated event based on pygame events

                if event.type == QUIT:
                    newEvent = ProgramQuitEvent()

                
                elif event.type == KEYDOWN:
                    pass
                    
                elif event.type == pygame.MOUSEBUTTONDOWN: # all the mouse down events
                    clickPosition = pygame.mouse.get_pos() # gets position of mouse when clicked
                    newEvent = MouseClickEvent(clickPosition)


                    

                if newEvent: # if there is an event
                    self.eventManager.post(newEvent)
                    
            pressed = pygame.key.get_pressed()
            directionX = pressed[K_d] - pressed[K_a]
            directionY = pressed[K_s] - pressed[K_w]
            
            #package the direction details
            textDirectionX = ''
            textDirectionY = ''
            if directionX == -1:
                textDirectionX = 'LEFT'
            elif directionX == 1:
                textDirectionX = 'RIGHT'
            if directionY == -1:
                textDirectionY = 'UP'
            elif directionY == 1:
                textDirectionY = 'DOWN'
                
            textDirection = textDirectionX + textDirectionY
            if textDirection:# if the user pressed a direction
                newEvent = CharacterMoveRequestEvent(textDirection)
                self.eventManager.post(newEvent) # send it


                
class FrameRateTicker():
    '''
    sends events to the event manager to update all event listeners
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.FPS = 50
        self.running = True

    def run(self):
        event = TickEvent()
        self.eventManager.post(event)
        # call this function again
        if self.running == True:
            reactor.callLater((1 / self.FPS), self.run)
        else:
            reactor.stop()


    def notify(self, event):
        if isinstance(event, ProgramQuitEvent): # if we got a quit program event
            self.running = False
            
#-------------------------------------------------------------------------------

class Game():
    ''' Generates GameStartedEvent() on the first TickEvent'''
    
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.players = [Player(eventManager)]

        self.state = 'preparing'
    def _start(self):
        self.state = 'running'
        newEvent = GameStartedEvent(self)
        self.eventManager.post(newEvent)

    def notify(self, event):
        if isinstance(event, TickEvent):
            if self.state == 'preparing':
                self._start()


class Player(object):
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.game = None
        self.name = ''
        self.eventManager.register_listener(self)
        
        self.character = CharacterObject(eventManager)

    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))

    def notify(self, event):
        pass        

class CharacterObject():
    '''
    user controlled character

    input creates move request event
    event is posted
    character OBJECT is notified of event
    runs character.move
    character checks if its possible to move in the direction
    runs move calculations
    gets new position
    creates character move event
    posts event
    game display is notified of event
    runs gamedisplay.move_character
    gets SPRITE character from the gamedisplay group using the OBJECT character
    gets position of the OBJECT character
    sets the SPRITE moveTo position to the OBJECT position

    
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.startingX = 100
        self.startingY = 100
        self.trueX = 100 # holds the true position values
        self.trueY = 100
        self.speed = 3
        self.position = (self.trueX, self.trueY)
        self.movementDirection = None



    def _move(self, direction):
        # check if we can move in the direction
        if direction == 'UP':
            self.trueY -= self.speed
        elif direction == 'DOWN':
            self.trueY += self.speed
        elif direction == 'LEFT':
            self.trueX -= self.speed
        elif direction == 'RIGHT':
            self.trueX += self.speed
            
        elif direction == 'LEFTUP':
            self.trueX -= (self.speed * .707)
            self.trueY -= (self.speed * .707)
        elif direction == 'RIGHTUP':
            self.trueX += (self.speed * .707)
            self.trueY -= (self.speed * .707)
        elif direction == 'LEFTDOWN':
            self.trueX -= (self.speed * .707)
            self.trueY += (self.speed * .707)
        elif direction == 'RIGHTDOWN':
            self.trueX += (self.speed * .707)
            self.trueY += (self.speed * .707)
            
        self.position = (self.trueX, self.trueY)
        newEvent = CharacterMoveEvent(self)
        self.eventManager.post(newEvent)



    def _spawn(self):
        position = (self.startingX,self.startingY) # is this used???
        newEvent = CharacterSpawnEvent(self)
        self.eventManager.post(newEvent)



    def notify(self, event):
        if isinstance(event, CharacterMoveRequestEvent):
            self._move(event.direction)

        elif isinstance(event, GameStartedEvent):
            self._spawn()

        elif isinstance(event, MouseClickEvent):
            pass


class CharacterSprite(pygame.sprite.Sprite):
    '''
    sprite that represents the character image
    '''
    def __init__(self, group=None):
        pygame.sprite.Sprite.__init__(self, group)

        self.image = pygame.image.load(os.path.join('resources','character.png')).convert()
        self.rect = self.image.get_rect()
        self.newPosition = None
        self.rect.center = (200,200)

    def update(self):
        if self.newPosition:
            self.rect.center = self.newPosition
            self.newPosition = None


class GameDisplay():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        pygame.init()
        self.screen = pygame.display.set_mode((1024, 576))
        pygame.display.set_caption('Defense RPG')
        self.background = pygame.Surface(self.screen.get_size()) # replace with map
        self.background.fill((21, 153, 220))

        # sprite groups
        self.characterSpritesGroup = pygame.sprite.RenderUpdates()
        
    def _spawn_character(self, character):
        position = character.position
        characterSprite = CharacterSprite(self.characterSpritesGroup)
        characterSprite.rect.center = position

    def _move_character(self, character):
        position = character.position
        characterSprite = self._get_character_sprite(character)
        characterSprite.newPosition = position

    def _get_character_sprite(self, character):
        #group only contains one
        for c in self.characterSpritesGroup:
            return c
        return None

    def notify(self, event):
        if isinstance(event, TickEvent):
            # draw all the images to the screen
            self.screen.blit(self.background, (0, 0))
            self.characterSpritesGroup.update()
            self.characterSpritesGroup.draw(self.screen)
            pygame.display.flip()
            
        elif isinstance(event, CharacterSpawnEvent):
            self._spawn_character(event.character)

        elif isinstance(event, CharacterMoveEvent):
            self._move_character(event.character)


def package_events(event):
    pickled_event = ''
    pickle.dump(event, pickled_event)
    unpickled_event = pickle.load(pickled_event)
    print unpickled_event
    
    
    
    


class ClientProtocol(protocol.Protocol):
        
    def connectionMade(self):
        self.transport.write("Connection successful")
        
    
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print "just got data from the server:", data
    
    def connectionLost(self, reason):
        print "connection lost"
        print reason

    def notify(self, event):
        if event.name == 'Tick Event':
            pass
        else:
            package_events(event)
            self.transport.write('hey! this is player 1')


class ClientFactory(protocol.ClientFactory):
    def __init__(self, eventManager):
        self.protocol = ClientProtocol
        self.protocolInstance = None
        
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def buildProtocol(self, address):
        ''' Catches the building protocol,
        so we can create an instance to it'''
        self.protocolInstance = ClientProtocol()
        print '...Protocol Built'
        return self.protocolInstance

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - Exiting"
        print reason
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost - Exiting"
        print reason

    def startedConnecting(self, connector):
        print 'Started connecting'
        print connector

    def notify(self, event):
        if self.protocolInstance:
            self.protocolInstance.notify(event)



def main():

    print '#######################################'
    print '##### Starting Defense RPG Client #####'
    print '#######################################'
    print 'Loading...'
    
    # start pygame stuff
    eventManager = EventManager()
    
    inputController = InputController(eventManager)
    frameRateTicker = FrameRateTicker(eventManager)
    gameDisplay = GameDisplay(eventManager)
    game = Game(eventManager)

    factory = ClientFactory(eventManager)
    reactor.connectTCP('localhost', 24100, factory)
    print '...Loading Complete'
    print 'Running Reactor...'
    reactor.callWhenRunning(frameRateTicker.run)
    
    reactor.run()
        
if __name__ == '__main__':
    main()
    pygame.quit()


