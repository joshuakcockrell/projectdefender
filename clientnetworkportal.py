from twisted.internet import protocol
from twisted.internet import reactor
from twisted.protocols import amp
from twisted.internet.error import ConnectionDone

import events
from serverfactory import RemoteTextMessageEvent
from serverfactory import RemoteCompleteGameStateRequestEvent
from serverfactory import RemoteChangedGameStateRequestEvent
from serverfactory import RemoteUserKeyboardInputEvent
from serverfactory import RemotePlaceWallRequestEvent
from serverfactory import RemoteShootProjectileRequestEvent

class ClientProtocol(amp.AMP):
    def __init__(self, eventManager, eventEncoder):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)

        self.eventEncoder = eventEncoder

    def connectionMade(self):
        '''Called when a connection is made. '''
        print 'Connected to: ' + str(self.transport.realAddress)
        event = events.ConnectedToServerEvent()
        self.eventManager.post(event)

    def send_message(self, event):
        if event.send_over_network == True:
            # only send if we are still connected
            if self.transport:
                if event.name == 'Text Message Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.callRemote(RemoteTextMessageEvent, message = list_to_send)
                    remoteCall.addCallback(self.MessageReceived) # do we need this?
                    remoteCall.addErrback(self.ErrorCallback)

                elif event.name == 'User Keyboard Input Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.callRemote(RemoteUserKeyboardInputEvent,
                                                        message = encoded_event)
                    remoteCall.addCallback(self.InputReceived)
                    remoteCall.addErrback(self.ErrorCallback)

                elif event.name == 'Place Wall Request Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.callRemote(RemotePlaceWallRequestEvent,
                                                        message = encoded_event)
                    remoteCall.addCallback(self.InputReceived)
                    remoteCall.addErrback(self.ErrorCallback)

                elif event.name == 'Shoot Projectile Request Event':
                    encoded_event = self.eventEncoder.encode_event(event)
                    remoteCall = self.callRemote(RemoteShootProjectileRequestEvent,
                                                        message = encoded_event)
                    remoteCall.addErrback(self.ErrorCallback)

                elif event.name == 'Complete Game State Request Event':
                    remoteCall = self.callRemote(RemoteCompleteGameStateRequestEvent, message = event.name)
                    remoteCall.addCallback(self.CompleteGameStateReceived)
                    remoteCall.addErrback(self.ErrorCallback)
                    
                elif event.name == 'Changed Game State Request Event':
                    remoteCall = self.callRemote(RemoteChangedGameStateRequestEvent, message = event.name)
                    remoteCall.addCallback(self.ChangedGameStateReceived)
                    remoteCall.addErrback(self.ErrorCallback)
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
        event = events.CompleteGameStateEvent(game_state['response'])
        self.eventManager.post(event)

    def ChangedGameStateReceived(self, game_state):
        ''' This is added as a callback when sending a game update request '''
        event = events.ChangedGameStateEvent(game_state['response'])
        self.eventManager.post(event)

    def ErrorCallback(self, failure):
        '''if the remotecall goes wrong, this is added as an error back'''
        #print 'Error callback received, reason: ' + str(failure)
        pass

    def notify(self, event):
        self.send_message(event)
        
class ClientFactory(protocol.ClientFactory):
    def __init__(self, eventManager, eventEncoder, ip_address, port):
        self.eventManager = eventManager
        self.eventEncoder = eventEncoder
        self.protocol = ClientProtocol

    def test(self, iconnector):
        print 'test, connector: ' + str(iconnector)

    def reconnect(self):
        self.connector.connect()
        print 'attempted to reconnect'
        
    def startedConnecting(self, connector):
        print 'Connecting to server...'
        
    def clientConnectionFailed(self, connector, reason):
        print '...Connection failed: ' + str(reason.getErrorMessage())
        self.connector = connector
        # send ourself so we can use ourself to reconnect
        event = events.ConnectionFailedEvent(self)
        self.eventManager.post(event)

    def clientConnectionLost(self, connector, reason):
        print 'Connection lost: ' + str(reason.getErrorMessage())
        event = events.ConnectionLostEvent()
        self.eventManager.post(event)

    def buildProtocol(self, addr):
        '''we override this so that we can send the event manager along'''
        p = self.protocol(self.eventManager, self.eventEncoder)
        p.factory = self
        return p
        

class ClientConnector():
    def __init__(self, eventManager, eventEncoder, ip_address='localhost', port=5887):
        self.ip_address = ip_address
        self.port = port
        self.eventManager = eventManager
        self.eventManager.add_listener(self)
        
        self.clientFactory = ClientFactory(eventManager, eventEncoder, ip_address, port)

    def connect(self):
        self.connection = reactor.connectTCP(self.ip_address, self.port, self.clientFactory, timeout=5)

    def disconnect(self):
        self.connection.disconnect()

    def notify(self, event):
        if event.name == 'Stop Network Connection Event':
            self.disconnect()
    '''
    connection = protocol.ClientCreator(reactor, amp.AMP).connectTCP(ip_address, 12345)
    connection.addCallback(messageSender.connected)
    '''
