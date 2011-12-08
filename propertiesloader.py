class UnknownValue(Exception):
    def __init__(self, command, value):
        self.command = command
        self.value = value
    def __str__(self):
        return repr(str(self.command) + '=' + str(self.value))

class UnknownCommand(Exception):
    def __init__(self, command):
        self.command = command
    def __str__(self):
        return repr(self.command)

class PropertiesFileNotFound(Exception):
    def __init__(self, command):
        self.command = command
    def __str__(self):
        return repr(self.command)

def load_properties():
    ##### Loading from the properties file #####
    try:
        properties = open('properties.txt', 'r').readlines()
    except IOError:
        raise PropertiesFileNotFound('properties.txt')
    ip_address = None
    for line in properties:
        command = line.split('=')
        
        if command[0] == 'ip-address':
            ip_address = command[1]
            ip_address = ip_address.rstrip('\n') # get rid of the '\n'
        else:
            if command[0][0] != '#':
                raise UnknownCommand(command[0])
            
    return ip_address

if __name__ == '__main__':
    properties = load_properties()
    print properties
