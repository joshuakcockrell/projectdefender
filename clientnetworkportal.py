from twisted.internet.protocol import ClientCreator
from twisted.internet import reactor
from twisted.protocols import amp
from twisted.internet.error import ConnectionDone

import events
from serverfactory import RemoteTextMessageEvent
from serverfactory import RemoteCompleteGameStateRequestEvent
from serverfactory import RemoteUserKeyboardInputEvent
from serverfactory import RemotePlaceWallRequestEvent

class MessageSender():
    ''' This object is used to send messages over the wire'''
    def __init__(self, eventManager, eventEncoder):
        self.server = None # stores the server reference so we can send messages
        self.eventManager = eventManager
        self.eventManager.add_listener(self)
        self.eventEncoder = eventEncoder
        
    def connected(self, server):
        ''' When we connect to the server, we use this to
        store a reference to the server
        '''
        # this is a callback from the TCP connect
        print 'The server: ' + str(server)
        self.server = server # store the serverw

    # Sending to server
    def send_message(self, event):
        if event.send_over_network == True:
        # sends the message to the server
            if self.server: # if there is a server
                if event.name == 'Text Message Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.server.callRemote(RemoteTextMessageEvent, message = list_to_send)
                    remoteCall.addCallback(self.MessageReceived) # do we need this?

                elif event.name == 'User Keyboard Input Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.server.callRemote(RemoteUserKeyboardInputEvent,
                                                        message = encoded_event)
                    remoteCall.addCallback(self.InputReceived)

                elif event.name == 'Place Wall Request Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.server.callRemote(RemotePlaceWallRequestEvent,
                                                        message = encoded_event)
                    remoteCall.addCallback(self.InputReceived)

                elif event.name == 'Complete Game State Request Event':
                    remoteCall = self.server.callRemote(RemoteCompleteGameStateRequestEvent, message = event.name)
                    remoteCall.addCallback(self.CompleteGameStateReceived)
                else:
                    print 'The event <' + event.name + '> cannot be sent over the network!'
                    
    # Receiving from server
    def MessageReceived(self, message):
        ''' This is added as a callback when sending a text message '''
        pass

    def InputReceived(self, message):
        ''' This is added as a callback when sending an input message '''
        pass

    def CompleteGameStateReceived(self, game_state):
        ''' This is added as a callback when sending a game update request '''
        event = events.CharacterStatesEvent(game_state['response'])
        self.eventManager.post(event)
                
    def notify(self, event):
        self.send_message(event)

def connect_to_server(messageSender):
    connection = ClientCreator(reactor, amp.AMP).connectTCP('localhost', 12345)
    connection.addCallback(messageSender.connected)
