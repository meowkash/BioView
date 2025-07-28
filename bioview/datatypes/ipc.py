'''
A collection of commands that can be sent to and responses that can be received from backend processes. 
'''
import time 
from enum import Enum 

class Message:
    def __init__(self, msg_type, value=None, id=None):
        self.msg_type = msg_type
        self.value = value
        self.id = id or int(time.time() * 1000)

class ResponseType(Enum): 
    STATUS = 'status' # Connection status 
    DISPLAY = 'display' # Data sent for display (graphical or otherwise)
    ERROR = 'error' # Error to be logged
    INFO = 'info' # Information to be logged
    WARNING = 'warning' # Warnings to be shown 
    DEBUG = 'debug' # Debugging
    
class CommandType(Enum): 
    CONNECT = 'connect' # Init 
    START = 'start' # Start data acquisition
    STOP = 'stop' # Stop data acquisition
    SAVE = 'save' # Enable/disable saving 
    SET_PARAM = 'set_param' # Update configuration parameter 
    DISCONNECT = 'disconnect' # Disconnect and remove 