# example amp client

from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp
from ampserver import ReceiveTextMessageEvent

class Event():
    '''
    superclass for events
    '''
    def __init__(self):
        self.name = 'Default Event'

class TextMessageEvent(Event):
    ''' Just text '''
    def __init__(self, text):
        self.name = 'Text Message Event'
        self.text = text

class EventCreator():
    def __init__(self):
        pass

    def create_text_message_event(self, text):
        return {'name': 'Text Message Event', 'text': text}
        

def MessageReceived(message):
    ''' This is added as a callback when sending a message '''
    pass
    # print 'message received from the server: ' + message['response']


class MessageSender():
    ''' The message generator uses this object to send messages '''
    def __init__(self, eventManager, eventCreator):
        self.server = None # stores the server reference so we can send messages
        eventManager.add_listener(self)
        #self.eventCreator = eventCreator
        
    def connected(self, server):
        ''' When we connect to the server, we use this to
        store a reference to the server
        '''
        # this is a callback from the TCP connect
        self.server = server # store the server

    def send_message(self, event):
        # sends the message to the server
        if self.server: # if there is a server
            # different types of events we would want to send
            if event['name'] == 'Text Message Event':
                list_to_send = [{'name': 'Text Message Event', 'text': 'text'}]
                list_to_send.append(event)
                remoteCall = self.server.callRemote(ReceiveTextMessageEvent, message=list_to_send)
                remoteCall.addCallback(MessageReceived) # do we need this?

    def notify(self, event):
        # the message generator calls this after it generates a message
        self.send_message(event)







        
class EventManager():
    '''
    Loops every second and sends a message to the message sender
    '''
    def __init__(self, eventCreator):
        self.listeners = [] # holds our listeners
        self.eventCreator = eventCreator

    def add_listener(self, listener):
        '''
        add a listener to our list so we can send stuff to it
        '''
        self.listeners.append(listener)

    def run(self):
        # sends a message every second
        # create an event
        event = self.eventCreator.create_text_message_event('Hi bum')
        for listener in self.listeners:
            listener.notify(event)
        reactor.callLater(1, self.run)



if __name__ == '__main__':
    # creates messages to send every one second
    eventCreator = EventCreator()
    eventManager = EventManager(eventCreator)
    # class responsible for sending messages to the server
    messagesender = MessageSender(eventManager, eventCreator)


    connection = ClientCreator(reactor, amp.AMP).connectTCP('localhost', 12345)
    connection.addCallback(messagesender.connected)
    eventManager.run()
    reactor.run()

