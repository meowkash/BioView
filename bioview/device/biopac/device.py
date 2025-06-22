import queue

from bioview.types import Device
from bioview.device.common import DisplayWorker, SaveWorker
from bioview.types import ConnectionStatus, DataSource
from .config import BiopacConfiguration

# Core functionality that should always be available
from .connect import ConnectWorker
from .process import ProcessWorker
from .receive import ReceiveWorker

class BiopacDevice(Device):    
    def __init__(
        self,
        device_name,
        config: BiopacConfiguration,
        save: bool = False,
        save_path=None,
        display=False,
    ):
        super().__init__(
            device_name=device_name,
            config=config,
            device_type="biopac",
            save=save,
            save_path=save_path,
            display=display,
        )

        self.rx_queue = queue.Queue()

    def _populate_data_sources(self):
        # Generate channel labels:data queue index mapping alongwith absolute channel numbers
        for idx, _ in enumerate(self.config.channels):
            label = f"Ch{idx + 1}"
            source = DataSource(device=self, channel=idx, label=label)
            self.data_sources.append(source)

            self.config.absolute_channel_nums[idx] = idx

    def connect(self):
        self.connect_thread = ConnectWorker(self.config)
        self.connect_thread.initSucceeded.connect(self._on_connect_succeess)
        self.connect_thread.initFailed.connect(self._on_connect_failure)
        self.connect_thread.logEvent.connect(self._log_message)

        self.connect_thread.start()
        self.connect_thread.wait()

    def run(self):
        if self.handler is None:
            self.logEvent.emit("error", "No BIOPAC object found")
            return

        # Start receiving
        self.threads["Receive"] = ReceiveWorker(
            biopac=self.handler, config=self.config, rx_queue=self.rx_queue
        )

        self.num_channels = len(self.config.channels)

        # Start saving
        if self.save and self.save_path is not None:
            self.threads["Save"] = SaveWorker(
                save_path=self.save_path,
                data_queue=self.save_queue,
                num_channels=self.num_channels,
                running=True,
            )

        # Create display thread
        if self.display and self.display_sources is not None:
            self.threads["Display"] = DisplayWorker(
                config=self.config,
                data_queue=self.display_queue,
                running=True,
            )
            self.threads["Display"].dataReady.connect(self._update_display)

        # Start threads
        super().run()

    def stop(self):
        return super().stop()

    def balance_gains(self):
        pass

    def sweep_frequency(self):
        pass

    def _on_connect_succeess(self, biopac):
        self.handler = biopac

        # Update status bar
        self.connectionStateChanged.emit(ConnectionStatus.CONNECTED)
