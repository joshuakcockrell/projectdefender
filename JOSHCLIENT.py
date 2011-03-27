import os
from twisted.spread import pb
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.main import installReactor


server_to_client_events = []
client_to_server_events = []



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
        if not registry.has_key(state_dictionary




















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


