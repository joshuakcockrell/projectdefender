import cProfile

import programclock
import events
import clientdisplay
import propertiesloader
import userinputmanager
import mainmenu
import clientnetworkportal
import reconnectmenu
import ampclient

def connect_and_run_game():
    print 'sratringduddue'
    
    object_registry = {}
    clientConnector = clientnetworkportal.ClientConnector(eventManager, eventEncoder, ip_address)
    clientConnector.connect()

    clientView = clientdisplay.ClientDisplay(eventManager, object_registry)

    programClock.start_reactor()
    print 'reactor stopped'

    exit_reason = clientView.get_exit_reason()
    reconnectable_factory = clientView.get_reconnectable_factory()
    clientView.quit_pygame()
    print 'Returning to Main Menu...'
    return exit_reason

def reconnect_and_run_game(self):
    print 'RECONNECTING'
    clientView = ClientView(eventManager, object_registry)

    programClock = ProgramClock(eventManager)
    programClock.run()
    
    reconnectable_factory.reconnect()
    

eventEncoder = events.EventEncoder()
eventManager = events.EventManager()

programClock = programclock.ProgramClock(eventManager)
userInputManager = userinputmanager.UserInputManager(eventManager)

ip_address = propertiesloader.load_properties()


running = True
while running:
    if not mainmenu.run():
        running = False
    else:
        exit_reason = connect_and_run_game()
        
        if exit_reason == 'USERQUIT':
            running = False
        elif exit_reason == 'CONNECTIONFAILED':
            if not reconnectmenu.run(): # if we want to quit
                running = False
            else: # they want to reconnect
                clientOverlord.reconnect_and_run_game()
                running = False
        elif exit_reason == 'CONNECTIONLOST':
            pass
