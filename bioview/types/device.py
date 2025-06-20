import time
import queue
from multiprocessing import Process, Queue

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from bioview.types import DataSource, CommandType, Message, ResponseType

from .config import Configuration
from .status import ConnectionStatus

class DeviceProcess(Process): 
    def __init__(self, 
                 cmd_queue: Queue, 
                 data_queue: Queue, 
                 device, 
                 daemon = None, 
    ):
        super().__init__(daemon=daemon)
        self.cmd_queue = cmd_queue # Receives command from main
        self.data_queue = data_queue # Sends response to main 
        
        self.device = device 
        
        # Connect handlers 
        self.device.logEvent.connect(self.log_response)
        self.device.connectionStateChanged.connect(self.update_status)
        self.device.dataReady.connect(self.send_display)
        
    def listen(self): 
        try:
            cmd = self.cmd_queue.get_nowait()
            if not isinstance(cmd, Message):
                raise TypeError(f'Expected command to be of type bioview.types.Message but got {type(cmd)} instead')
            
            # Parse commands 
            if cmd.msg_type == CommandType.CONNECT:
                self.device.connect()
            elif cmd.msg_type == CommandType.START:
                self.device.run()
            elif cmd.msg_type == CommandType.STOP:
                self.device.stop()
            elif cmd.msg_type == CommandType.SAVE:
                self.device.save = True
                self.device.save_path = cmd.value
            elif cmd.msg_type == CommandType.SET_PARAM:
                pass # TODO: Implement
            elif cmd.msg_type == CommandType.DISCONNECT:
                self.running = False 
                self.stop()
        
        except queue.Empty:
            time.sleep(0.01) # Keep load low 
        except TypeError as e: 
            resp = Message(
                msg_type = ResponseType.ERROR, 
                value = str(e), 
            )
            self.respond(resp)
    
    def log_response(self, level, message): 
        if level == 'error': 
            msg_type = ResponseType.ERROR
        elif level == 'warning': 
            msg_type = ResponseType.WARNING
        elif level == 'info': 
            msg_type = ResponseType.INFO
        else: 
            msg_type = ResponseType.DEBUG
        
        resp = Message(
            msg_type = msg_type, 
            value = message
        )
        self.respond(resp)
    
    def update_status(self, status: ConnectionStatus):
        resp = Message(
            msg_type = ResponseType.STATUS, 
            value = status
        )
        self.respond(resp)
      
    def send_display(self, data: np.ndarray, source: DataSource): 
        resp = Message(
            msg_type = ResponseType.DISPLAY, 
            value = (data, source)
        )
        self.respond(resp)
    
    def respond(self, data):
        try: 
            if not isinstance(data, Message):
                raise TypeError(f'Expected data to be of type bioview.types.Message but got {type(data)} instead')
            
            self.data_queue.put_nowait()
        except queue.Full: 
            print('Unable to add to data queue as queue is full')
        except TypeError as e: 
            resp = Message(
                msg_type = ResponseType.ERROR, 
                value = str(e), 
            )
            self.data_queue.put_nowait(resp)
    
    def run(self): 
        self.running = True 
        while self.running: 
            self.listen()
    
    def stop(self): 
        self.join()
    
class Device(QObject):
    connectionStateChanged = pyqtSignal(ConnectionStatus)
    logEvent = pyqtSignal(str, str)
    dataReady = pyqtSignal(np.ndarray, DataSource)

    def __init__(
        self,
        config: Configuration,
        device_name: str,
        device_type: str,
        save: bool = False,
        save_path=None,
        display=True,
    ):
        super().__init__()
        self.device_name = device_name
        self.config = config
        self.device_type = device_type

        self.state = ConnectionStatus.DISCONNECTED

        self.handler = None

        self.threads = {}

        # Configuration for saving
        self.save = save
        self.save_path = save_path
        if self.save:
            self.save_queue = queue.Queue()
        else:
            self.save_queue = None

        # Configuration for display
        self.display = display
        if self.display:
            self.display_queue = queue.Queue()
        else:
            self.display_queue = None

        # Keep track of all data sources
        self.data_sources: list[DataSource] = []
        # Make data sources available, depending on config
        self._populate_data_sources()
        
    def _populate_data_sources(self):
        raise NotImplementedError  # We expect subclasses to implement this
    
    def get_disp_freq(self):
        return self.config.get_disp_freq()

    def connect(self):
        if getattr(self, "connect_thread", None) is not None:
            self.connect_thread.initFailed.connect(self._on_connect_failure)
            self.connect_thread.logEvent.connect(self._log_message)

            self.connectionStateChanged.emit(ConnectionStatus.CONNECTING)
            time.sleep(0.05)  # Small wait to ensure

            self.connect_thread.start()
            self.connect_thread.wait()
        else:
            return

    def run(self):
        for thread in self.threads.values():
            thread.logEvent.connect(self._log_message)
            thread.start()

    def stop(self):
        for thread in self.threads.values():
            thread.stop()

    def _on_connect_failure(self, msg):
        self.logEvent.emit("error", msg)
        self.connectionStateChanged.emit(ConnectionStatus.DISCONNECTED)

    def _log_message(self, level, msg):
        self.logEvent.emit(level, msg)

    def _update_display(self, data, source):
        self.dataReady.emit(data, source)
