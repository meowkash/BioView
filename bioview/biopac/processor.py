import queue

from PyQt6.QtCore import QThread

class ProcessWorker(QThread):
    def __init__(self, 
                 rx_queue: queue.Queue,
                 disp_queue: queue.Queue, 
                 running: bool = False, 
                 parent=None
    ):
        super().__init__(parent=parent)
        
        self.rx_queue = rx_queue
        self.running = running 
        
    def run(self): 
        while self.running:
            # Get latest sample 
            try:
            # Put processed sample into display queue 
            self.disp
    
    def stop(self):
        self.running = False 