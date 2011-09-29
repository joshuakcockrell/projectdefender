# example amp server

from twisted.protocols import amp

class ReceiveTextMessageEvent(amp.Command):
    ''' AMP command '''
    arguments = [('message', amp.AmpList([('name', amp.String()),
                                          ('text', amp.String())]))]
    #arguments = [('message', amp.String())] # not using this method
    response = [('response', amp.String())]

class ClientProtocol(amp.AMP):
    ''' This is an AMP protocol '''

    def receive_message(self, message):
        print 'Message received from the client: ' + str(message)
        return {'response': ''}

    ReceiveTextMessageEvent.responder(receive_message)# do we need this?

def main():
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory
    pf = Factory()
    pf.protocol = ClientProtocol
    reactor.listenTCP(12345, pf)
    print 'started'
    reactor.run()

if __name__ == '__main__':
    main()
