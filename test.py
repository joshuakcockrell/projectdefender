from twisted.internet import reactor
import time

def test():
    print 'hi'
    #reactor.stop()
    print 'k'

print 'started'
reactor.callLater(1, test)
reactor.callLater(2, test)
print 'called later'
reactor.run()
print 'returned'


time.sleep(3)
