import queue

from bioview.device import Device
from bioview.types import ConnectionStatus

# Core functionality that should always be available
from .controller import Controller as BiopacController
from .processor import ProcessWorker as BiopacProcessor
from .receiver import ReceiveWorker as BiopacReceiver


class BiopacDevice(Device):
    def __init__(self, config):
        super().__init__(device_type="biopac")
        self.config = config

        self.rx_queue = queue.Queue()

        self.data_mapping = {}

        self._generate_channel_mapping()

    def _generate_channel_mapping(self):
        # Generate channel labels:data queue index mapping alongwith absolute channel numbers
        for idx, _ in enumerate(self.config.channels):
            label = f"{self.config.device_name}_Ch{idx + 1}"
            self.data_mapping[label] = ("biopac", idx)
            self.config.absolute_channel_nums[idx] = idx

    def connect(self):
        self.connect_thread = BiopacController(self.config)
        self.connect_thread.initSucceeded.connect(self._on_connect_success)

        return super().connect()

    def run(self):
        if self.handler is None:
            self.logEvent.emit("error", "No BIOPAC object found")
            return

        # Create receiver thread
        self.threads["Receive"] = BiopacReceiver(
            biopac=self.handler, config=self.config, rx_queue=self.rx_queue
        )

        # Create save thread
        # self.threads['Save']

        # Create display thread
        # self.threads['Display']
        # self.threads['Display'].dataReady.connect(self.update_display)

        # Start threads
        super().run()

    def stop(self):
        return super().stop()

    def balance_gains(self):
        pass

    def sweep_frequency(self):
        pass

    def _on_connect_success(self, biopac):
        self.handler = biopac

        # Update status bar
        self.connectionState.emit(ConnectionStatus.CONNECTED)


def get_device_object(config):
    return BiopacDevice(config=config)


__all__ = ["BiopacDevice", "get_device_object"]
