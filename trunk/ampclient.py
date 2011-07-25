from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp
from ampserver import soup

def gotSoup(result):
    print 'got soup!'
    print result
    print result['response']

class MessageSender():
    def __init__(self, generator):
        self.server = None
        generator.add_listener(self)
        
    def connected(self, server):
        # this is a callback from the TCP connect
        self.server = server

    def send_stuff(self, message):
        # sends the message tot the server
        if self.server:
            remoteCall = self.server.callRemote(soup, message=message)
            remoteCall.addCallback(gotSoup)
            return remoteCall

    def notify(self, message):
        # the message generator calls this after it generates a message
        self.send_stuff(message)

        
class MessageGenerator():
    '''
    Loops every second and sends a message to the message sender
    '''
    def __init__(self):
        self.listeners = [] # holds our listeners

    def add_listener(self, listener):
        '''
        add a listener to our list so we can send stuff to it
        '''
        self.listeners.append(listener)

    def run(self):
        # sends a message every second
        for listener in self.listeners:
            listener.notify('hi bum')
        reactor.callLater(1, self.run)

if __name__ == '__main__':
    # creates messages to send every one second
    messagegenerator = MessageGenerator()
    # class responsible for sending messages to the server
    messagesender = MessageSender(messagegenerator)


    connection = ClientCreator(reactor, amp.AMP).connectTCP('localhost', 12345)
    connection.addCallback(messagesender.connected)
    messagegenerator.run()
    reactor.run()
