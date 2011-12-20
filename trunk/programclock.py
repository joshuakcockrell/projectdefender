import time
import pygame
from events import TickEvent

from twisted.internet import reactor


class ProgramClock():
    '''
    sends events to the event manager to update all event listeners
    uses python time.time() to get the delta time.
    The delta time (change in time since the last current time) is
    sent to the TickEvent. Different parts of the program use delta
    time to determine how far ahead it needs to step
    (this is used especially in the game physics)
    '''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)
            
        self.clock = pygame.time.Clock()
        self.initial_time = time.time()
        self.current_time = self.initial_time
        self.FPS = 60.0

        self.running = True
        
    def start_reactor(self):
        reactor.callLater(1.0, self.run)
        reactor.run()

    def stop_reactor(self):
        reactor.stop()

    def pause_reactor(self):
        self.running = False

    def unpause_reactor(self):
        self.running = True
        reactor.callLater(1.0, self.run)

    def run(self):
        if self.running == True:
            reactor.callLater((1.0 / self.FPS), self.run)

            self.last_time = self.current_time
            self.current_time = time.time()
            self.delta_time = self.current_time - self.last_time # get delta time

            event = TickEvent(self.delta_time)
            self.eventManager.post(event)

        else:
            print 'clock stopped running'
    

    def notify(self, event):
        if event.name == 'Stop Network Connection Event':
            self.running = False
