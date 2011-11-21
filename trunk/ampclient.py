# example amp client
# twisted imports
from twisted.internet import reactor

import time
import os
import math

import pygame
from pygame.locals import *

import events
import userinputmanager
import clientnetworkportal
import mapgrid

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

    def run(self):
        if self.running == True:
            reactor.callLater((1.0 / self.FPS), self.run)
        else:
            pass

        self.last_time = self.current_time
        self.current_time = time.time()
        self.delta_time = self.current_time - self.last_time # get delta time

        event = events.TickEvent(self.delta_time)
        self.eventManager.post(event)

        #event = RenderEvent()
        #self.eventManager.post(event)

    def _stop(self):
        self.running = False

    def notify(self, event):
        if event.name == 'Program Quit Event':
            self._stop()
        

class SpriteStatsDirectory():
    def __init__(self):
        pass

    def get_stats(self, object_type, desired_stats):
        pass

class Background(pygame.sprite.Sprite):
    def __init__(self, size, group = None):
        pygame.sprite.Sprite.__init__(self, group)
        
        self.image = pygame.Surface(size)
        self.image.fill((120, 235, 22))
        
        self.rect = self.image.get_rect()
        self.rect.topleft = ((0,0))

class WallSprite(pygame.sprite.Sprite):
    def __init__(self, object_id, object_position, object_velocity,
                 object_state, group = None):
        print 'new wall'
        pygame.sprite.Sprite.__init__(self, group)
        self.id = object_id

        self.state = object_state
        self._load_images()

        self.position = None
        self.velocity = object_velocity
        self.set_position(object_position)

    def _load_images(self):
        self.images = {}

        self.alive_image = pygame.image.load(os.path.join('resources','walltile.png'))
        self.alive_image.convert()

        self.dead_image = pygame.image.load(os.path.join('resources', 'walltile.png'))
        self.dead_image.convert()
        self.images['alive'] = self.alive_image
        self.images['dead'] = self.dead_image
        self.image = self.images[self.state]
        self.rect = self.image.get_rect()

    def set_position(self, position):
        self.position = position

    def set_velocity(self, velocity):
        self.velocity = velocity

    def set_state(self, object_state):
        self.object_state = object_state

    def is_dead(self):
        if self.object_state == 'alive':
            return False
        else:
            return True

    def update(self, delta_time):
        # if were already using the correct image
        if self.image == self.images[self.state]:
            pass
        else:
            # use the correct image
            self.image = self.images[self.state]
            self.rect = self.image.get_rect()
        # set the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.topleft = self.position


class EnemySprite(pygame.sprite.Sprite):
    def __init__(self, object_id, object_position, object_velocity,
                 object_state, group = None):
        print 'new enemy'
        pygame.sprite.Sprite.__init__(self, group)
        self.id = object_id

        self.state = object_state
        self._load_images()

        self.position = None
        self.velocity = object_velocity
        self.set_position(object_position)

    def _load_images(self):
        self.images = {}

        self.alive_image = pygame.image.load(os.path.join('resources','enemy.png'))
        self.alive_image.convert()

        self.dead_image = pygame.image.load(os.path.join('resources', 'enemy.png'))
        self.dead_image.convert()
        self.images['alive'] = self.alive_image
        self.images['dead'] = self.dead_image
        self.images['attacking'] = self.alive_image
        self.images['moving'] = self.alive_image
        self.images['roaming'] = self.alive_image
        self.image = self.images[self.state]
        self.rect = self.image.get_rect()

    def set_position(self, position):
        self.position = position

    def set_velocity(self, velocity):
        self.velocity = velocity

    def set_state(self, object_state):
        self.object_state = object_state

    def is_dead(self):
        if self.object_state == 'dead':
            return True
        else:
            return False

    def update(self, delta_time):
        # if were already using the correct image
        if self.image == self.images[self.state]:
            pass
        else:
            # use the correct image
            self.image = self.images[self.state]
            self.rect = self.image.get_rect()
        # set the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.topleft = self.position

          
class CharacterSprite(pygame.sprite.Sprite):
    def __init__(self, object_id, object_position, object_velocity,
                 object_state, group = None):
        print 'new character'
        pygame.sprite.Sprite.__init__(self, group)
        self.id = object_id

        self.state = object_state
        self._load_images()

        self.position = None
        self.velocity = object_velocity
        self.set_position(object_position)

    def _load_images(self):
        self.images = {}

        self.alive_image = pygame.image.load(os.path.join('resources','player.png'))
        self.alive_image.convert()

        self.dead_image = pygame.image.load(os.path.join('resources', 'player.png'))
        self.dead_image.convert()
        self.images['alive'] = self.alive_image
        self.images['dead'] = self.dead_image
        self.image = self.images[self.state]
        self.rect = self.image.get_rect()

    def set_position(self, position):
        self.position = position

    def set_velocity(self, velocity):
        self.velocity = velocity

    def set_state(self, object_state):
        self.object_state = object_state

    def is_dead(self):
        if self.object_state == 'alive':
            return False
        else:
            return True

    def update(self, delta_time):
        # if were already using the correct image
        if self.image == self.images[self.state]:
            pass
        else:
            # use the correct image
            self.image = self.images[self.state]
            self.rect = self.image.get_rect()
        # set the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.topleft = self.position


class ClientView():
    def __init__(self, eventManager, object_registry):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)

        self.map_dimensions = [25, 20]
        self.tile_size = 32
        self.screen_dimensions = [self.map_dimensions[0] * self.tile_size,
                                  self.map_dimensions[1] * self.tile_size]

        self._initialize_display(self.screen_dimensions)
        self.clock = pygame.time.Clock()

        self.sprite_stats_directory = SpriteStatsDirectory()

        self.user_controlled_character = None
        self.game_state_received = False

        self.object_registry = object_registry

        self.all_sprites = []
        self.background_sprites = pygame.sprite.RenderUpdates()
        self.wall_sprites = pygame.sprite.RenderUpdates()
        self.character_sprites = pygame.sprite.RenderUpdates()
        self.enemy_sprites = pygame.sprite.RenderUpdates()
        self.projectile_sprites = pygame.sprite.RenderUpdates()

        size = self.screen.get_size()
        Background(size, self.background_sprites)

        #self.collisionGrid = CollisionGrid(self.map_dimensions)

        self.user_placing_tower = True

    def _initialize_display(self, screen_dimensions):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_dimensions[0], screen_dimensions[1]))
        pygame.display.set_caption('Pygame Caption')

    def _handle_user_mouse_input(self, mouse_button, mouse_position):
        grid_position = mapgrid.convert_position_to_grid_position(mouse_position, self.tile_size)
        if mouse_button == 'LEFT':
            if self.user_placing_tower == True:
                event = events.PlaceWallRequestEvent(grid_position)
                self.eventManager.post(event)

        elif mouse_button == 'RIGHT':
            pass
      
    def _add_object_to_game(self, object_type, object_id, object_position,
                            object_velocity, object_state):
        if object_type == 'character':
            characterSprite = CharacterSprite(object_id, object_position,
                                               object_velocity, object_state,
                                               self.character_sprites)
            self.all_sprites.append(characterSprite)
            self.object_registry[object_id] = characterSprite

        elif object_type == 'enemy':
            enemySprite = EnemySprite(object_id, object_position,
                                      object_velocity, object_state,
                                      self.enemy_sprites)
            self.all_sprites.append(enemySprite)
            self.object_registry[object_id] = enemySprite

        elif object_type == 'wall':
            # server sends us back the walls position based on a grid
            grid_position = object_position
            object_position = mapgrid.convert_grid_position_to_position(grid_position, self.tile_size)
            
            wallSprite = WallSprite(object_id, object_position,
                                    object_velocity, object_state,
                                    self.wall_sprites)
            self.all_sprites.append(wallSprite)
            self.object_registry[object_id] = wallSprite

        
    def _update_game_state(self, object_states):
        # recieved a list of game objects (characters, projectiles, etc...)
        # example of game state list
        # [['CHARACTER', 19376408, [300, 300]], ['CHARACTER', 19377248, [300, 300]]]
        for object_state in object_states:
            object_type = object_state['object_type']
            object_id = object_state['object_id']
            object_position = object_state['object_position']
            object_velocity = object_state['object_velocity']
            object_state = object_state['object_state']

            if object_id in self.object_registry:
                current_object = self.object_registry[object_id] # get the object

                # handle is the server sent us a grid position
                if object_type in ['wall']:
                    grid_position = object_position
                    object_position = mapgrid.convert_grid_position_to_position(grid_position, self.tile_size)
                current_object.set_position(object_position)
                current_object.set_velocity(object_velocity)
                current_object.set_state(object_state)

                if current_object.is_dead():
                    current_object.kill()
                    self.object_registry.pop(object_id)
            # if the object does not exist
            else:
                self._add_object_to_game(object_type, object_id, object_position,
                                         object_velocity, object_state)
                
    def _update_objects(self, delta_time):
        for s in self.all_sprites:
            s.update(delta_time)

    def _render_display(self):
        self.background_sprites.draw(self.screen)
        self.wall_sprites.draw(self.screen)
        self.enemy_sprites.draw(self.screen)
        self.character_sprites.draw(self.screen)
        pygame.display.flip()
        # render everything
        


    def notify(self, event):
        if event.name == 'Tick Event':
            self._update_objects(event.delta_time)
            self._render_display()

            event = events.CompleteGameStateRequestEvent()
            self.eventManager.post(event)

        elif event.name == 'Character States Event':
            self._update_game_state(event.character_states)

        elif event.name == 'User Mouse Input Event':
            mouse_button = event.mouse_button
            mouse_position = event.mouse_position
            self._handle_user_mouse_input(mouse_button, mouse_position)
            
if __name__ == '__main__':
    object_registry = {}
    # creates messages to send every one second
    eventEncoder = events.EventEncoder()
    eventManager = events.EventManager()

    programClock = ProgramClock(eventManager)
    userInputManager = userinputmanager.UserInputManager(eventManager)

    clientView = ClientView(eventManager, object_registry)
    
    # class responsible for sending messages to the server
    messageSender = clientnetworkportal.MessageSender(eventManager, eventEncoder)
    clientnetworkportal.connect_to_server(messageSender)
    programClock.run()
    reactor.run()

