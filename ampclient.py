# example amp client
# twisted imports
from twisted.internet import reactor

import time
import os
import math
import random

import pygame
from pygame.locals import *

import rabbyt

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

class ClientSpriteObject(rabbyt.Sprite):
    def __init__(self, screen_dimensions, object_state, object_id=None):

        rabbyt.Sprite.__init__(self, texture=None)

        self.screen_dimensions = screen_dimensions
        self.id = object_id
        self.state = object_state
        self.position = None
        self.velocity = None

        self.textures = {}
        self.rot = 0 # rabbyt texture rotation
        self.alpha = 1
        
        self.particles = []

    def set_position(self, position):
        self.position = [position[0], position[1]]

    def set_velocity(self, velocity):
        self.velocity = [velocity[0], velocity[1]]

    def set_state(self, object_state):
        self.state = object_state
        if object_state == 'pending removal':
            raise RuntimeError('Incorrect object state: ' + str(object_state))

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_texture(self, state=None):
        if state:
            self.texture = self.textures[state]
        else:
            # check if were using the correct texture
            if self.texture != self.textures[self.state]:
                # use the correct texture
                self.texture = self.textures[self.state]

    def set_render_position(self):
        texture_width = self.get_width()
        texture_height = self.get_height()
        
        self.x = (self.position[0] - (self.screen_dimensions[0] / 2) + (texture_width / 2))
        self.y = (( -1 * self.position[1]) + (self.screen_dimensions[1] / 2) - (texture_width / 2))

    def get_width(self):
        return self.right - self.left

    def get_height(self):
        return self.top - self.bottom
    
    def render(self):
        self.set_render_position()
        rabbyt.Sprite.render(self)
        if self.particles:
            rabbyt.render_unsorted(self.particles)

    def _load_textures(self):
        ''' This function should be overridden'''
        pass

    def update(self):
        ''' This function should be overridden'''
        pass

class Particle(ClientSpriteObject):
    def __init__(self, screen_dimensions, object_state, object_position):
        ClientSpriteObject.__init__(self, screen_dimensions, object_state)

        self._load_textures()
        self.set_texture()

        self.speed = .001
        object_velocity = self._get_random_velocity()
        
        self.set_position(object_position)
        self.set_velocity(object_velocity)
        self.set_alpha(.5)

    def _load_textures(self):
        self.textures['alive'] = os.path.join('resources', 'blackbullet.png')

    def _get_random_velocity(self):
        velocity_x = random.random() * random.choice([-1, 1])
        velocity_y = random.random() * random.choice([-1, 1])
        return (velocity_x, velocity_y)

    def is_pending_removal(self):
        if self.state == 'pending removal':
            return True

    def update(self):
        if self.state != 'pending removal':
            self.position[0] += self.velocity[0]
            self.position[1] += self.velocity[1]

            self.alpha -= .01
            if self.alpha <= 0:
                self.state = 'pending removal'        

        
class WallSprite(ClientSpriteObject):
    def __init__(self, screen_dimensions, object_id, object_state,
                 object_position, object_velocity):

        ClientSpriteObject.__init__(self, screen_dimensions, object_state, object_id)

        self._load_textures()
        self.set_texture()
        
        self.set_position(object_position)
        self.set_velocity(object_velocity)
        
        self.dead_timer = 3

        print 'New wall... id: ' + str(self.id)

    def _load_textures(self):
        self.textures['alive'] = os.path.join('resources','walltile.png')
        self.textures['dead'] = os.path.join('resources', 'fire.png')

    def update(self, delta_time):
        # dont update if were pending removal
        if self.state == 'pending removal':
            return

        if self.state == 'dead':
            self.dead_timer -= delta_time
            if self.dead_timer <= 0:
                self.state = 'pending removal'
                return
        
        self.set_texture()
            
        # set the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        

class EnemySprite(ClientSpriteObject):
    def __init__(self, screen_dimensions, object_id, object_state,
                 object_position, object_velocity):

        ClientSpriteObject.__init__(self, screen_dimensions, object_state, object_id)
        
        self._load_textures()
        self.set_texture()

        self.set_position(object_position)
        self.set_velocity(object_velocity)
        
        print 'New enemy... id: ' + str(self.id)

    def _load_textures(self):
        self.textures['alive'] = os.path.join('resources','enemy.png')
        self.textures['dead'] = os.path.join('resources','enemy.png')
        self.textures['attacking'] = os.path.join('resources','enemy.png')
        self.textures['moving'] = os.path.join('resources','enemy.png')
        self.textures['roaming'] = os.path.join('resources','enemy.png')

    def spawn_particles(self):
        center_position = (self.position[0] + (self.get_width() / 2),
                           self.position[1] + (self.get_height() / 2))
        particle = Particle(self.screen_dimensions, 'alive', center_position)
        self.particles.append(particle)

    def update(self, delta_time):
        # dont update if were pending removal
        if self.state == 'pending removal':
            return

        if self.state == 'attacking':
            self.spawn_particles()
        
        self.set_texture()
            
        # set the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        for p in self.particles:
            p.update()
            if p.is_pending_removal():
                 self.particles.remove(p)
          
class CharacterSprite(ClientSpriteObject):
    def __init__(self, screen_dimensions, object_id, object_state,
                 object_position, object_velocity):

        ClientSpriteObject.__init__(self, screen_dimensions, object_state, object_id)
        
        self._load_textures()
        self.set_texture()

        self.set_position(object_position)
        self.set_velocity(object_velocity)

        print 'New character... id: ' + str(self.id)

    def _load_textures(self):
        self.textures['alive'] = os.path.join('resources','player.png')
        self.textures['dead'] = os.path.join('resources', 'player.png')

    def update(self, delta_time):
        # dont update if were pending removal
        if self.state == 'pending removal':
            return
        
        self.set_texture()
        
        # set the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

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

        self.background_sprites = []
        self.wall_sprites = []
        self.character_sprites = []
        self.enemy_sprites = []
        self.projectile_sprites = []

        self.user_placing_tower = True

    def _initialize_display(self, screen_dimensions):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_dimensions[0], screen_dimensions[1]),
                                              pygame.OPENGL | pygame.DOUBLEBUF)
        # rabbyt stuff
        rabbyt.set_viewport((screen_dimensions[0], screen_dimensions[1]))
        rabbyt.set_default_attribs()
        pygame.display.set_caption('Project Defender')

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
            characterSprite = CharacterSprite(self.screen_dimensions, object_id, object_state,
                                              object_position, object_velocity)
            self.character_sprites.append(characterSprite)
            self.object_registry[object_id] = characterSprite

        elif object_type == 'enemy':
            enemySprite = EnemySprite(self.screen_dimensions, object_id, object_state,
                                      object_position, object_velocity)
            self.enemy_sprites.append(enemySprite)
            self.object_registry[object_id] = enemySprite

        elif object_type == 'wall':
            # server sends us back the walls position based on a grid
            grid_position = object_position
            object_position = mapgrid.convert_grid_position_to_position(grid_position, self.tile_size)
            
            wallSprite = WallSprite(self.screen_dimensions, object_id, object_state,
                                    object_position, object_velocity)
            self.wall_sprites.append(wallSprite)
            self.object_registry[object_id] = wallSprite
        
    def _update_game_state(self, object_packages):
        # recieved a list of game objects (characters, projectiles, etc...)
        for object_package in object_packages:
            object_type = object_package['object_type']
            object_id = object_package['object_id']
            object_position = object_package['object_position']
            object_velocity = object_package['object_velocity']
            object_state = object_package['object_state']

            if object_id in self.object_registry:
                current_object = self.object_registry[object_id] # get the object

                # handle is the server sent us a grid position
                if object_type in ['wall']:
                    grid_position = object_position
                    object_position = mapgrid.convert_grid_position_to_position(grid_position, self.tile_size)
                current_object.set_position(object_position)
                current_object.set_velocity(object_velocity)
                current_object.set_state(object_state)

            # if the object does not exist
            else:
                self._add_object_to_game(object_type, object_id, object_position,
                                         object_velocity, object_state)
                
    def _update_objects(self, delta_time):              
        for w in self.wall_sprites:
            w.update(delta_time)
            if w.state == 'pending removal':
                self.wall_sprites.remove(w)
                del self.object_registry[w.id]

        for e in self.enemy_sprites:
            e.update(delta_time)
            if e.state == 'pending removal':
                self.enemy_sprites.remove(e)
                del self.object_registry[e.id]

        for c in self.character_sprites:
            c.update(delta_time)
            if c.state == 'pending removal':
                self.character_sprites.remove(c)
                del self.object_registry[w.id]
                
    def _render_display(self):
        rabbyt.clear((.2,.4,.7))
        
        for b in self.background_sprites:
            b.render()

        for w in self.wall_sprites:
            w.render()

        for e in self.enemy_sprites:
            e.render()
            
        for c in self.character_sprites:
            c.render()

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

