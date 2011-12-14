import cProfile
    
import mainmenu
import reconnectmenu
import ampclient

clientOverlord = ampclient.ClientOverlord()

running = True
while running:
    if not mainmenu.run():
        running = False
    else:
        exit_reason = clientOverlord.run()
        if exit_reason == 'USERQUIT':
            running = False
        elif exit_reason == 'CONNECTIONFAILED':
            if not reconnectmenu.run(): # if we want to quit
                running = False
            else: # they want to reconnect
                clientOverlord.reconnect_and_run()
                running = False
        elif exit_reason == 'CONNECTIONLOST':
            pass
