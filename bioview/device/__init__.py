import time
import numpy as np
import queue
from multiprocessing import Process, Queue

from PyQt6.QtCore import QProcess
from bioview.types import (
    Configuration,
    ExperimentConfiguration,
    CommandType, 
    Message, 
    ResponseType,
    ConnectionStatus,
    DataSource
)

from .usrp import MultiUsrpConfiguration, UsrpConfiguration
from .biopac import BiopacConfiguration

class DeviceProcess(QProcess):
    def __init__(
        self,
        id: str, 
        config: Configuration, 
        exp_config: ExperimentConfiguration,
        cmd_queue: Queue,
        data_queue: Queue,
        save: bool
    ):
        super().__init__()
        self.cmd_queue = cmd_queue  # Receives command from main
        self.data_queue = data_queue  # Sends response to main
        self.id = id
        self.config = config 
        self.save = save 
        self.exp_config = exp_config
        
    
    def listen(self):
        try:
            cmd = self.cmd_queue.get_nowait()
            if not isinstance(cmd, Message):
                raise TypeError(
                    f"Expected command to be of type bioview.types.Message but got {type(cmd)} instead"
                )

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
                pass  # TODO: Implement
            elif cmd.msg_type == CommandType.DISCONNECT:
                self.running = False
                self.stop()

        except queue.Empty:
            time.sleep(0.1)  # Keep load low
        except TypeError as e:
            resp = Message(
                msg_type=ResponseType.ERROR,
                value=str(e),
            )
            self.respond(resp)

    def log_response(self, level, message):
        if level == "error":
            msg_type = ResponseType.ERROR
        elif level == "warning":
            msg_type = ResponseType.WARNING
        elif level == "info":
            msg_type = ResponseType.INFO
        else:
            msg_type = ResponseType.DEBUG

        resp = Message(msg_type=msg_type, value=message)
        self.respond(resp)

    def update_status(self, status: ConnectionStatus):
        resp = Message(msg_type=ResponseType.STATUS, value=(self.id, status))
        self.respond(resp)

    def send_display(self, data: np.ndarray, source: DataSource):
        resp = Message(msg_type=ResponseType.DISPLAY, value=(data, source))
        self.respond(resp)

    def respond(self, data):
        try:
            if not isinstance(data, Message):
                raise TypeError(
                    f"Expected response to be of type bioview.types.Message but got {type(data)} instead"
                )

            self.data_queue.put_nowait(data)
        except queue.Full:
            print("Unable to add to data queue as queue is full")
        except TypeError as e:
            resp = Message(
                msg_type=ResponseType.ERROR,
                value=str(e),
            )
            self.data_queue.put_nowait(resp)

    def run(self):
        self.running = True
        
        self.device = get_device_object(
            device_name = self.id, 
            config=self.config,
            save = self.save,
            exp_config=self.exp_config
        ) 
        
        # Connect handlers
        self.device.logEvent.connect(self.log_response)
        self.device.connectionStateChanged.connect(self.update_status)
        self.device.dataReady.connect(self.send_display)
        
        while self.running:
            self.listen()

    def stop(self):
        self.running = False

def _check_type(obj, typ):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return all(isinstance(x, typ) for x in obj)

    return isinstance(obj, typ)


def get_device_object(device_name, config, save, exp_config: ExperimentConfiguration):
    if _check_type(config, MultiUsrpConfiguration):
        from .usrp import get_device_object

        return get_device_object(
            device_name=device_name,
            config=config,
            save=save,
            save_path=exp_config.get_save_path(device_name),
        )
    elif _check_type(config, BiopacConfiguration):
        from .biopac import get_device_object

        return get_device_object(
            device_name=device_name,
            config=config,
            save=save,
            save_path=exp_config.get_save_path(device_name),
        )
    else:
        return None


__all__ = ["MultiUsrpConfiguration", "BiopacConfiguration", "get_device_object"]
