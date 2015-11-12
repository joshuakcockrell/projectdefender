# example amp client
# twisted imports
from twisted.internet import reactor

import time
import os
import math
import random
from random import getrandbits #speed up or particle stuff

import pygame
from pygame.locals import *

import rabbyt

import events
import userinputmanager

import mapgrid

class ClientSpriteObject(rabbyt.Sprite):
    def __init__(self, screen_dimensions, object_state, object_id=None):

        rabbyt.Sprite.__init__(self, texture=None)

        self.screen_dimensions = screen_dimensions
        self.half_screen_width = self.screen_dimensions[0] / 2
        self.half_screen_height = self.screen_dimensions[1] / 2
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

    def set_center_position(self, position):
        '''takes a topleft position and makes it so the center is at that point'''
        texture_width = self.get_width()
        texture_height = self.get_height()

        # transform our center position so its at the same spot as our topleft
        new_topleft_position = (position[0] - (texture_width / 2),
                                position[1] - (texture_height / 2))

        self.position = [new_topleft_position[0], new_topleft_position[1]]

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
                
        self.texture_width = self.get_width()
        self.texture_height = self.get_height()
        self.half_texture_width = self.texture_width / 2
        self.half_texture_height = self.texture_height / 2

    def set_render_position(self):
        self.x = (self.position[0] - self.half_screen_width + self.half_texture_width)
        self.y = (( -1 * self.position[1]) + self.half_screen_height - self.half_texture_width)

    def get_width(self):
        return self.right - self.left

    def get_height(self):
        return self.top - self.bottom
    
    def render(self):
        if self.state != 'dead':
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
    def __init__(self, screen_dimensions, particle_type, object_state, object_position):
        ClientSpriteObject.__init__(self, screen_dimensions, object_state)

        self.particle_type = particle_type
        self._load_textures()
        self.set_texture()

        self.speed = 50
        self.decay_time = 2.0
        object_velocity = self._get_random_velocity()

        self.set_center_position(object_position)
        self.set_velocity(object_velocity)
        self.set_alpha(.5)

    def _load_textures(self):
        if self.particle_type == 'basic':
            self.textures['alive'] = os.path.join('resources', 'yellowbullet.png')
        elif self.particle_type == 'glitter':
            self.textures['alive'] = os.path.join('resources', 'yellowbullet.png')
        self._set_default_color()
    def _get_random_velocity(self):
        velocity_x = (random.random() * random.choice([-1, 1]) * self.speed)
        velocity_y = (random.random() * random.choice([-1, 1]) * self.speed)
        return (velocity_x, velocity_y)

    def is_pending_removal(self):
        if self.state == 'pending removal':
            return True

    def _set_default_color(self):
        self.red = 0.0
        self.green = 0.0
        self.blue = 0.0
    def _set_random_texture(self):
        # SOO SLOW
        if getrandbits(1):
            self.red = 0.0
            self.green = 0.0
            self.blue = 0.0
        else:
            self.red = 0.0
            self.green = 0.8
            self.blue = 0.0        

    def update(self, delta_time):
        if self.state != 'pending removal':
            self.position[0] += self.velocity[0] * delta_time
            self.position[1] += self.velocity[1] * delta_time

            self.alpha -= delta_time / self.decay_time
            if self.alpha <= 0:
                self.state = 'pending removal'

        self._set_random_texture()
        
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
        self.position[0] += self.velocity[0] * delta_time
        self.position[1] += self.velocity[1] * delta_time

class ProjectileSprite(ClientSpriteObject):
    def __init__(self, screen_dimensions, object_id, object_state,
                 object_position, object_velocity):
        ClientSpriteObject.__init__(self, screen_dimensions, object_state, object_id)

        self._load_textures()
        self.set_texture()

        self.particle_timer = 0.0
        self.time_between_particles = .05

        self.set_position(object_position)
        self.set_velocity(object_velocity)

        print 'New Projectile... id: ' + str(self.id)

    def _load_textures(self):
        self.textures['alive'] = os.path.join('resources','blackbullet.png')
        self.textures['dead'] = os.path.join('resources','blackbullet.png')

    def spawn_particles(self, delta_time):
        self.particle_timer += delta_time
        center_position = (self.position[0] + (self.get_width() / 2),
                               self.position[1] + (self.get_height() / 2))
        
        while self.particle_timer >= self.time_between_particles:
            self.particle_timer -= self.time_between_particles
            particle = Particle(self.screen_dimensions, 'glitter', 'alive', center_position)
            self.particles.append(particle)

    def update(self, delta_time):
        self.previous_state = self.state
        if self.state in self.textures:
            # dont update if were pending removal
            if self.state == 'pending removal':
                return

            for p in self.particles:
                    p.update(delta_time)
                    if p.is_pending_removal():
                         self.particles.remove(p)

            if self.state == 'dead':
                if len(self.particles) <= 0:
                    self.state = 'pending removal'

            else:
            
                self.set_texture()
                self.spawn_particles(delta_time)
                    
                # set the position
                self.position[0] += self.velocity[0] * delta_time
                self.position[1] += self.velocity[1] * delta_time
        else:
            self.state = self.previous_state

'''
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
        particle = Particle(self.screen_dimensions, 'basic', 'alive', center_position)
        self.particles.append(particle)

    def update(self, delta_time):
        # dont update if were pending removal
        if self.state == 'pending removal':
            return

        if self.state == 'attacking':
            pass
            #self.spawn_particles()
        
        self.set_texture()
            
        # set the position
        self.position[0] += self.velocity[0] * delta_time
        self.position[1] += self.velocity[1] * delta_time

        for p in self.particles:
            p.update(delta_time)
            if p.is_pending_removal():
                 self.particles.remove(p)
'''         
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
        self.position[0] += self.velocity[0] * delta_time
        self.position[1] += self.velocity[1] * delta_time

class ClientDisplay():
    def __init__(self, eventManager, object_registry):
        self.eventManager = eventManager
        self.eventManager.add_listener(self)

        self.map_dimensions = [25, 20]
        self.tile_size = 32
        self.screen_dimensions = [self.map_dimensions[0] * self.tile_size,
                                  self.map_dimensions[1] * self.tile_size]

        self._initialize_display(self.screen_dimensions)
        self.clock = pygame.time.Clock()

        self.exit_reason = None

        self.user_controlled_character = None
        self.initial_game_state_received = False

        self.object_registry = object_registry

        self.background_sprites = []
        self.wall_sprites = []
        self.character_sprites = []
        self.enemy_sprites = []
        self.projectile_sprites = []

        self.user_placing_tower = True

    def _initialize_display(self, screen_dimensions):
        print 'INIT DISPLAY'
        pygame.init()
        self.screen = pygame.display.set_mode((screen_dimensions[0], screen_dimensions[1]),
                                              pygame.OPENGL | pygame.DOUBLEBUF)
        # rabbyt stuff
        rabbyt.set_viewport((screen_dimensions[0], screen_dimensions[1]))
        rabbyt.set_default_attribs()
        pygame.display.set_caption('Project Defender')

    def quit_pygame(self):
        '''so we can call this after everything else'''
        print 'PYGAME QUIT'
        pygame.quit()
        
    def _quit_program(self, reason, reconnectable_factory=None):
        self.exit_reason = reason
        self.reconnectable_factory = reconnectable_factory
        print 'Stopping Network Connection...'
        print 'reason' + str(self.exit_reason)

    def get_exit_reason(self):
        if self.exit_reason:
            return self.exit_reason
        else:
            raise RuntimeError('No exit reason: ' + str(self.exit_reason))

    def get_reconnectable_factory(self):
        return self.reconnectable_factory

    def _handle_user_mouse_input(self, mouse_button, mouse_position):
        grid_position = mapgrid.convert_position_to_grid_position(mouse_position, self.tile_size)
        if mouse_button == 'LEFT':
            event = events.ShootProjectileRequestEvent(mouse_position)
            self.eventManager.post(event)

        elif mouse_button == 'RIGHT':
            if self.user_placing_tower == True:
                event = events.PlaceWallRequestEvent(grid_position)
                self.eventManager.post(event)
      
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

        elif object_type == 'projectile':
            projectileSprite = ProjectileSprite(self.screen_dimensions, object_id, object_state,
                                                object_position, object_velocity)
            self.projectile_sprites.append(projectileSprite)
            self.object_registry[object_id] = projectileSprite
        
    def _update_game_state(self, object_packages):
        # recieved a list of game objects (characters, projectiles, etc...)
        for object_package in object_packages:
            object_type = object_package['object_type']
            object_id = object_package['object_id']
            object_position = object_package['object_position']
            object_velocity = object_package['object_velocity']
            object_state = object_package['object_state']

            if object_type != 'default':

                if object_id in self.object_registry:
                    current_object = self.object_registry[object_id] # get the object

                    # handle if the server sent us a grid position
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

        for p in self.projectile_sprites:
            p.update(delta_time)
            if p.state == 'pending removal':
                self.projectile_sprites.remove(p)
                del self.object_registry[p.id]
                
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

        for p in self.projectile_sprites:
            p.render()

        pygame.display.flip()
        # render everything

    def notify(self, event):
        if event.name == 'Tick Event':
            self._update_objects(event.delta_time)
            self._render_display()

            # ask for a full game state
            if not self.initial_game_state_received:
                event = events.CompleteGameStateRequestEvent()
                self.eventManager.post(event)
            else:
                event = events.ChangedGameStateRequestEvent()
                self.eventManager.post(event)

        elif event.name == 'User Quit Event':
            self._quit_program('USERQUIT')
            event = events.StopNetworkConnectionEvent()
            self.eventManager.post(event)

        elif event.name == 'Connection Failed Event':
            self._quit_program('CONNECTIONFAILED', event.reconnectable_factory)
            event = events.StopNetworkConnectionEvent()
            self.eventManager.post(event)
            
        elif event.name == 'Connection Lost Event':
            self._quit_program('CONNECTIONLOST')
            event = events.StopNetworkConnectionEvent()
            self.eventManager.post(event)
            
        elif event.name == 'Complete Game State Event':
            self.initial_game_state_received = True
            self._update_game_state(event.complete_game_state)

        elif event.name == 'Changed Game State Event':
            self._update_game_state(event.changed_game_state)

        elif event.name == 'User Mouse Input Event':
            mouse_button = event.mouse_button
            mouse_position = event.mouse_position
            self._handle_user_mouse_input(mouse_button, mouse_position)
        
