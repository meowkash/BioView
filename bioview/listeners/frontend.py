import time 
import numpy as np
import multiprocessing as mp
from PyQt6.QtCore import QObject, pyqtSignal

from bioview.datatypes import DataSource, ConnectionStatus, Message, ResponseType

class FrontendListener(QObject):
    logEvent = pyqtSignal(str, str)  # (Level, Message)
    dataReady = pyqtSignal(np.ndarray, DataSource)  # (Data, Source)
    connectionStateChanged = pyqtSignal(str, ConnectionStatus)  # (Device Name, State)

    # Signals to send to the main thread
    def __init__(self, data_queue: mp.Queue, resp_queue: mp.Queue, parent=None):
        super().__init__(parent)
        self.data_queue = data_queue
        self.resp_queue = resp_queue

    def start(self):
        self.running = True
        
        while self.running:
            try:
                # Get responses for logging, status change, etc 
                if not self.resp_queue.empty(): 
                    resp = self.resp_queue.get_nowait()

                    if resp.msg_type == ResponseType.ERROR:
                        self.logEvent.emit("error", resp.value)
                    elif resp.msg_type == ResponseType.WARNING:
                        self.logEvent.emit("warning", resp.value)
                    elif resp.msg_type == ResponseType.INFO:
                        self.logEvent.emit("info", resp.value)
                    elif resp.msg_type == ResponseType.DEBUG:
                        self.logEvent.emit("debug", resp.value)
                    elif resp.msg_type == ResponseType.STATUS:
                        self.connectionStateChanged.emit(resp.value[0], resp.value[1])
                
                # Get data for display
                if not self.data_queue.empty():
                    resp = self.data_queue.get_nowait()
                    if resp.msg_type == ResponseType.DISPLAY:
                        self.dataReady.emit("error", resp.value[0], resp.value[1])
            except Exception:
                time.sleep(0.001)

    def stop(self):
        self.running = False