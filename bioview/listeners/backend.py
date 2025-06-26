import queue
import multiprocessing as mp

from bioview.types import Configuration, ExperimentConfiguration, CommandType, Message, DataSource, ResponseType, ConnectionStatus
from bioview.device import get_device_object

class BackendListener(mp.Process):
    def __init__(
        self,
        id: str, 
        config: Configuration, 
        exp_config: ExperimentConfiguration,
        cmd_queue: mp.Queue, # Command passed from frontend to backend
        resp_queue: mp.Queue, # Response passed from backend to frontend
        data_queue: mp.Queue, # Data passed from backend to frontend
        save: bool
    ):
        super().__init__()
        self.id = id
        self.config = config 
        self.exp_config = exp_config
        
        self.cmd_queue = cmd_queue  # Receives command from frontend
        self.resp_queue = resp_queue
        self.data_queue = data_queue  # Sends data from frontend to backend
        
        self.save = save 
        self.device = None 
        self.listener_thread = None
    
    def run(self):
        self.running = True
        
        self.device = get_device_object(
            device_name = self.id, 
            config=self.config,
            resp_queue=self.resp_queue, 
            data_queue=self.data_queue, 
            save = self.save,
            exp_config=self.exp_config
        ) 
        
        while self.running:
            try: 
                # Get commands from frontend 
                if not self.cmd_queue.empty(): 
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
                        self.device.disconnect()
                        
            except Exception as e:
                resp = Message(
                    msg_type=ResponseType.ERROR,
                    value=str(e),
                )
                try: 
                    self.resp_queue.put_nowait(resp)
                except queue.Full: 
                    print('Unable to add to response queue as it is full.')

    def stop(self):
        self.running = False
        