# generates random items based on an enemy level

import random

class ItemGenerator():
    def __init__(self):

        self.item_level = None
        self.item_names = ['dagger', 'sword']
        self.item_base_damages = {'dagger': 2, 'sword': 3}
        self.item_base_attack_speeds = {'dagger': 5, 'sword': 2}
        self.random_stats = ['fire', 'ice']
        
    def generate_item(self, item_level):

        generated_item = random.choice(self.item_names)
        random_seed = random.random()
        random_seed += 1
        random_seed /= 3
        
        generated_item_damage = self.item_base_damages[generated_item] * item_level
        generated_item_damage *= random_seed
        rounded_item_damage = round(generated_item_damage)

        generated_item_attack_speed = self.item_base_attack_speeds[generated_item] * item_level
        generated_item_attack_speed *= random_seed
        rounded_item_attack_speed = round(generated_item_attack_speed)
        
        
        return [generated_item, rounded_item_damage, rounded_item_attack_speed]
    
if __name__ == '__main__':
    item_generator = ItemGenerator()
    enemy_level = random.randint(1, 20)
    print 'You killed a level ' + str(enemy_level) + ' enemy!'
    new_item = item_generator.generate_item(enemy_level)
    print 'heres your new item stats: '
    print 'name: ' + new_item[0]
    print 'damage: ' + str(new_item[1])
    print 'attack_speed: ' + str(new_item[2])
