import queue

from bioview.device import Device
from bioview.types import ConnectionStatus

# Core functionality that should always be available
from .connect import ConnectWorker
from .process import ProcessWorker
from .receive import ReceiveWorker


class BiopacDevice(Device):
    def __init__(self, config, exp_config, save=False, display=False):
        super().__init__(device_type="biopac", exp_config=exp_config, save=save)
        self.config = config

        self.rx_queue = queue.Queue()

        self._generate_channel_mapping()

    def _generate_channel_mapping(self):
        # Generate channel labels:data queue index mapping alongwith absolute channel numbers
        for idx, _ in enumerate(self.config.channels):
            label = f"{self.config.device_name}_Ch{idx + 1}"
            self.data_mapping[label] = ("biopac", idx)
            self.config.absolute_channel_nums[idx] = idx

    def connect(self):
        self.connect_thread = ConnectWorker(self.config)
        self.connect_thread.initSucceeded.connect(self._on_connect_success)

        return super().connect()

    def run(self):
        if self.handler is None:
            self.logEvent.emit("error", "No BIOPAC object found")
            return

        # Start receiving
        self.threads["Receive"] = ReceiveWorker(
            biopac=self.handler, config=self.config, rx_queue=self.rx_queue
        )

        self.num_channels = len(self.config.channels)

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
        self.connectionStateChanged.emit(ConnectionStatus.CONNECTED)


def get_device_object(config, exp_config):
    return BiopacDevice(config=config, exp_config=exp_config)


__all__ = ["BiopacDevice", "get_device_object"]
