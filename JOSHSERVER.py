from twisted.spread import pb
from twisted.internet import protocol


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



class EventManager():
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
        


class ServerEventManager(EventManager):
    '''subclass of event manager that doesn't wait for a Tick event to start
    processing the event queue (the server doesnt use Tick events)
    '''

    def __init__(self):
        EventManager.__init__(self)
        self._locked = False

    def post(self, event):
        EventManager.post(self, event)
        if not self._lock:
            self._lock = True
            self._process_event_queue()
            self._lock = False

class NetworkClientController(pb.Root):
    '''gets events from the network'''
    def __init__(self, eventManager, shared_object_registry):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)
        self.shared_objects = shared_object_registry

    def remote_ClientConnect(self, netClient):
        new_event = ClientConnectEvent(netClient)
        self.eventManager.post(new_event)

    def remote_GetObjectState(self, objectID):
        if not self.shared_objects.has_key(objectID):
            return [0,0] # WHAAA?
        object_dict = self.shared_objects[objectID].get_state_to_copy()
        return [objectID, object_dict]

    def remote_EventOverNetwork(self, event):
        # server gets an event
        self.eventManager.post(event)
        return True

    def notify(self, event):
        # do nothing when notified
        pass


class TextLogView(object):
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

    def notify(self, event):
        if isinstance(event, TickEvent):
            return

        print event.name, event


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
            if not hasattr(network, copyable_class_name):
                return
            copyable_class = getattr(network, copyable_class_name)
            testing_event = copyableClass(testing_event, self.shared_objects)

        if testing_event.__class__ not in network.serverToClientEvents:
            # not gonna send that
            return

        for c in self.clients:
            print 'Sending Event: ' + str(testing_event)
            remoteCall = client.callRemote('ServerEvent', testing_event)

class Player():
    '''A person playing the game'''
    def __init__(self, eventManager):
        self.eventManager = eventManager

        self.characters = [Character(eventManager)]

class Character():
    '''Game State object that holds Character Logic
    (not visuals or user input)
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.position = (300, 300)

    def notify(self, event):
        pass

class Game():
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.register_listener(self)

        self.state = 'PREPARING'

        self.players = [Player(eventManager)]

    def start(self):
        self.state = 'RUNNING'
        new_event = GameStatedEvent(self)
        self.eventManager.post(new_event)

    def notify(self, event):
        if isinstance(event, GameStartRequestEvent):
            if self.state == 'RUNNING':
                self.start()
    


            

def main():
    print '#######################################'
    print '##### Starting Defense RPG Server #####'
    print '#######################################'
    print 'Loading...'
    
    eventManager = ServerEventManager()
    shared_object_registry = {}
    log = TextLogView(eventManager)
    clientController = NetworkClientController(eventManager, shared_object_registry)
    clientView = NetworkClientView(eventManager, shared_object_registry)
    game = Game(eventManager)

    from twisted.internet import reactor

   
    
    reactor.listenTCP(24100, pb.PBServerFactory(clientController))

    print 'Loading Complete!'
    print 'Running Reactor...'
    reactor.run()


if __name__ == '__main__':
    main()
