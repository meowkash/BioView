import time

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from bioview.types import ConnectionStatus


class Device(QObject):
    connectionStateChanged = pyqtSignal(ConnectionStatus)
    logEvent = pyqtSignal(str, str)
    dataReady = pyqtSignal(np.ndarray)

    def __init__(self, device_type: str):
        super().__init__()
        self.device_type = device_type

        self.state = ConnectionStatus.DISCONNECTED

        self.handler = None
        self.threads = {}

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

    def _update_state(self, state):
        pass
