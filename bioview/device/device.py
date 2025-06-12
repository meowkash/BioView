import queue
import time

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from bioview.device.common import DisplayWorker, SaveWorker
from bioview.types import ConnectionStatus


class Device(QObject):
    connectionStateChanged = pyqtSignal(ConnectionStatus)
    logEvent = pyqtSignal(str, str)
    dataReady = pyqtSignal(np.ndarray)

    def __init__(self, device_type: str, exp_config, save: bool):
        super().__init__()
        self.device_type = device_type
        self.exp_config = exp_config
        self.save = save

        self.state = ConnectionStatus.DISCONNECTED

        self.handler = None

        self.threads = {}

        if self.save:
            self.save_queue = queue.Queue()
        else:
            self.save_queue = None

        self.display_queue = queue.Queue()

        self.data_mapping = {}

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
        # Start saving
        if self.exp_config is not None:
            if self.save:
                self.threads["Save"] = SaveWorker(
                    save_path=self.exp_config.get_save_path(self.device_type),
                    data_queue=self.save_queue,
                    num_channels=self.num_channels,
                    running=True,
                )

            # Create display thread
            self.threads["Display"] = DisplayWorker(
                data_queue=self.display_queue,
                disp_ds=self.exp_config.disp_ds[self.device_type],
                disp_channels=self.exp_config.disp_channels[self.device_type],
                disp_filter_spec=self.exp_config.disp_filter_spec[self.device_type],
                running=True,
            )
            self.threads["Display"].dataReady.connect(self._update_display)

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

    def _update_state(self, state):
        pass

    def _update_display(self, data):
        self.dataReady.emit(data)
