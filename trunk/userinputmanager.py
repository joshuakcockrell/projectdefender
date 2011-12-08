import pygame
from pygame.locals import *

import events

class UserInputManager():
    ''' gets user input from the mouse and keyboard'''
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)
        self.shooting = True

    def notify(self, event):
        if event.name == 'Tick Event':
            #go through the user input
            for event in pygame.event.get():
                newEvent = None
                if event.type == QUIT:
                    newEvent = ProgramQuitEvent()
                    self.eventManager.post(newEvent)
                    
                elif event.type == KEYDOWN:
                    if event.key in [pygame.K_ESCAPE]:
                        newEvent = ProgramQuitEvent()
                        self.eventManager.post(newEvent)

                elif event.type == pygame.MOUSEBUTTONDOWN: # all the mouse down events
                    if event.button == 3: # right mouse button
                        print 'pressed the right mouse button'
                        self.shooting = False
                        mouse_button = 'RIGHT'
                        mouse_position = event.pos
                        newEvent = events.UserMouseInputEvent(mouse_button, mouse_position)

                    elif event.button == 1: # left mouse button
                        self.shooting = True
                        mouse_button = 'LEFT'
                        mouse_position = event.pos
                        newEvent = events.UserMouseInputEvent(mouse_button, mouse_position)

                # shoot a lot
                #if self.shooting == True:
                    #newEvent = UserMouseInputEvent('LEFT', pygame.mouse.get_pos())


                if newEvent:
                    self.eventManager.post(newEvent)
                

            #getting arrow key movement
            pressed = pygame.key.get_pressed()
            direction_x = pressed[K_d] - pressed[K_a]
            direction_y = pressed[K_s] - pressed[K_w]
            
            # ready the direction details
            text_direction_x = ''
            text_direction_y = ''
            text_direction = ''
            
            if direction_x == -1:
                text_direction_x = 'LEFT'
            elif direction_x == 1:
                text_direction_x = 'RIGHT'
            if direction_y == -1:
                text_direction_y = 'UP'
            elif direction_y == 1:
                text_direction_y = 'DOWN'
                
            text_direction = text_direction_x + text_direction_y # put direction into a string
            if text_direction:# if the user pressed a direction
                newEvent = events.UserKeyboardInputEvent(text_direction)
                self.eventManager.post(newEvent)
