from twisted.protocols import amp

class soup(amp.Command):
    arguments = [('message', amp.String())]
    response = [('response', amp.String())]

class Math(amp.AMP):

    def recieve_message(self, message):
        print 'WE GOT A MESSAGE' + message
        return {'response': 'Message received: ' + message}

    soup.responder(recieve_message)

def main():
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory
    pf = Factory()
    pf.protocol = Math
    reactor.listenTCP(12345, pf)
    print 'started'
    reactor.run()

if __name__ == '__main__':
    main()
