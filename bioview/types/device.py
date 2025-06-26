import queue

import numpy as np

from .config import Configuration
from .datasource import DataSource
from .status import ConnectionStatus
from .ipc import Message, ResponseType

from bioview.utils import emit_signal

class Device:
    def __init__(
        self,
        config: Configuration,
        device_name: str,
        device_type: str,
        resp_queue,
        data_queue,
        save: bool = False,
        save_path=None,
        display=True,
    ):
        super().__init__()
        self.device_name = device_name # This serves as ID
        self.config = config
        self.device_type = device_type

        self.state = ConnectionStatus.DISCONNECTED
        self.resp_queue = resp_queue
        self.data_queue = data_queue
        
        self.handler = None

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
            
    def log_event(self, level, message):
        if level == "error":
            msg_type = ResponseType.ERROR
        elif level == "warning":
            msg_type = ResponseType.WARNING
        elif level == "info":
            msg_type = ResponseType.INFO
        else:
            msg_type = ResponseType.DEBUG

        resp = Message(msg_type=msg_type, value=message)
        try: 
            self.resp_queue.put_nowait(resp)
        except queue.Full: 
            print('Unable to add to response queue as it is full.')
    
    def connection_state_changed(self, status: ConnectionStatus):
        resp = Message(msg_type=ResponseType.STATUS, value=(getattr(self, 'device_name', 0), status))
        
        try: 
            self.resp_queue.put_nowait(resp)
        except queue.Full: 
            print('Unable to add to response queue as it is full.')
    
    def data_ready(self, data: np.ndarray, source: DataSource):
        resp = Message(msg_type=ResponseType.DISPLAY, value=(data, source))
        
        try: 
            self.data_queue.put_nowait(resp)
        except queue.Full: 
            print('Unable to add to data queue as it is full.')
    
    def _populate_data_sources(self):
        raise NotImplementedError  # We expect subclasses to implement this

    def get_disp_freq(self):
        return self.config.get_disp_freq()

    def connect(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def _on_connect_success(self):
        emit_signal(self.connection_state_changed, ConnectionStatus.CONNECTED)

    def _on_connect_failure(self, msg):
        emit_signal(self.log_event, "error", msg)
        emit_signal(self.connection_state_changed, ConnectionStatus.DISCONNECTED)