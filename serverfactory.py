from twisted.internet.protocol import Factory
from twisted.protocols import amp

import events


class ServerFactory(Factory):
    # this has been overridden so we can send the event manager to
    # the protocol instance
    def __init__(self, eventManager):
        self.protocol_instance = None
        self.eventManager = eventManager

    def buildProtocol(self, addr):
        """Create an instance of a subclass of Protocol.

        The returned instance will handle input on an incoming server
        connection, and an attribute \"factory\" pointing to the creating
        factory.

        Override this method to alter how Protocol instances get created.

        @param addr: an object implementing L{twisted.internet.interfaces.IAddress}
        """
        # this has been overridden so we can send the event manager to
        # the protocol instance
        p = self.protocol(self.eventManager)
        p.factory = self
        return p      


class RemoteTextMessageEvent(amp.Command):
    ''' AMP command '''
    #requriesAnswer = False
    arguments = [('message', amp.AmpList([('name', amp.String()),
                                          ('text', amp.String())]))]
    response = [('response', amp.String())]

class RemoteUserKeyboardInputEvent(amp.Command):
    #requiresAnswer = False
    arguments = [('message', amp.AmpList([('name', amp.String()),
                                          ('input', amp.String())]))]
    response = [('response', amp.String())]

class RemotePlaceWallRequestEvent(amp.Command):
    arguments = [('message', amp.AmpList([('name', amp.String()),
                                          ('grid_position', amp.ListOf(amp.Integer()))]))]
    response = [('response', amp.String())]

class RemoteShootProjectileRequestEvent(amp.Command):
    arguments = [('message', amp.AmpList([('name', amp.String()),
                                          ('destination position', amp.ListOf(amp.Integer()))]))]
    
class RemoteCompleteGameStateRequestEvent(amp.Command):
    arguments = [('message', amp.String())]
    response = [('response', amp.AmpList([('object_type', amp.String()),
                                          ('object_id', amp.Integer()),
                                          ('object_position', amp.ListOf(amp.Integer())),
                                          ('object_velocity', amp.ListOf(amp.Float())),
                                          ('object_state', amp.String())]))]

class RemoteChangedGameStateRequestEvent(amp.Command):
    arguments = [('message', amp.String())]
    response = [('response', amp.AmpList([('object_type', amp.String()),
                                          ('object_id', amp.Integer()),
                                          ('object_position', amp.ListOf(amp.Integer())),
                                          ('object_velocity', amp.ListOf(amp.Float())),
                                          ('object_state', amp.String())]))]
    
class ClientConnectionProtocol(amp.AMP):
    '''
    This is an AMP protocol
    each protocol represents a connection to a client
    new protocols are made for every new connection
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)
        self.eventEncoder = events.EventEncoder()
        self.complete_game_state = None
        self.changed_game_state = None
        self.client_number = None # set in connectionMade()
        self.client_ip = None # set in connectionMade()
        self.client_port = None # set in connectionMade()

    def connectionMade(self):
        '''Called when a connection is made. '''
        self.client_number = self.transport.sessionno
        self.client_ip = self.transport.client[0]
        self.client_port = self.transport.client[1]
        # tell server someone has connected
        print 'New client #' + str(self.client_number) + str(self.transport.client)
        event = events.NewClientConnectedEvent(self.client_number, self.client_ip)
        self.eventManager.post(event)

    def disconnect(self):
        self.transport.loseConnection()
        
    def _getPeer():
        return self.transport.getPeer()

    def _getHost():
        return self.transport.getHost()

    def remote_text_message_event(self, message):
        print 'Message received from the client: ' + str(message)
        return {'response': ''}
    RemoteTextMessageEvent.responder(remote_text_message_event)

    def remote_user_keyboard_input_event(self, message):
        event = self.eventEncoder.decode_event(message, self.client_number)
        self.eventManager.post(event)

        return {'response': ''}
    RemoteUserKeyboardInputEvent.responder(remote_user_keyboard_input_event)

    def remote_place_wall_request_event(self, message):
        event = self.eventEncoder.decode_event(message, self.client_number)
        self.eventManager.post(event)

        return {'response': ''}
    RemotePlaceWallRequestEvent.responder(remote_place_wall_request_event)

    def remote_shoot_projectile_request_event(self, message):
        event = self.eventEncoder.decode_event(message, self.client_number)
        self.eventManager.post(event)

        return {'response': ''}
    RemoteShootProjectileRequestEvent.responder(remote_shoot_projectile_request_event)
    
    def remote_complete_game_state_request_event(self, message):
        if self.complete_game_state:
            return {'response': self.complete_game_state}
        else:
            raise RuntimeWarning('No game state! ' + str(self.complete_game_state))
    RemoteCompleteGameStateRequestEvent.responder(remote_complete_game_state_request_event)

    def remote_changed_game_state_request_event(self, message):
        if self.changed_game_state:
            return {'response': self.changed_game_state}
        else:
            raise RuntimeWarning('No game state! ' + str(self.changed_game_state))
    RemoteChangedGameStateRequestEvent.responder(remote_changed_game_state_request_event)
    
    def remote_character_move_request_event(self, message):
        event = events.CharacterMoveRequestEvent()
    
    def update_complete_game_state(self, event):
        self.complete_game_state = event.complete_game_state

    def update_changed_game_state(self, event):
        self.changed_game_state = event.changed_game_state
        
    def notify(self, event):
        if event.name == 'Complete Game State Event':
            self.update_complete_game_state(event)

        elif event.name == 'Changed Game State Event':
            self.update_changed_game_state(event)

        elif event.name == 'Server Quit Event':
            self.disconnect()
            
    
