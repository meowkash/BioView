import queue

from PyQt6.QtCore import QThread

from bioview.types import ExperimentConfiguration, BiopacConfiguration

class ProcessWorker(QThread):
    def __init__(self, 
                 exp_config: ExperimentConfiguration,
                 rx_queue: queue.Queue,
                 disp_queue: queue.Queue, 
                 running: bool = False, 
                 parent=None
    ):
        super().__init__(parent=parent)
        self.exp_config = exp_config
        
        self.rx_queue = rx_queue
        self.disp_queue = disp_queue
        self.running = running 
        
        self.out_file = exp_config.get_save_path('usrp') 
        
    def run(self): 
        while self.running:
            # Get latest sample 
            try:
                pass 
            except: 
                pass 
            # Put processed sample into display queue 
            self.disp = None 
    
    def stop(self):
        self.running = False 