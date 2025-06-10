import queue
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal

from bioview.utils import get_filter, apply_filter
from bioview.types import ExperimentConfiguration

class DisplayWorker(QThread):
    dataReady = pyqtSignal(np.ndarray)
    logEvent = pyqtSignal(str, str)

    def __init__(self, 
                 config: ExperimentConfiguration, 
                 disp_queues: dict[queue.Queue], 
                 running: bool = True,
                 parent = None
        ):
        super().__init__(parent)
        self.config = config 
        self.disp_filter = get_filter(
            bounds = config.disp_filter_spec['bounds'], 
            samp_rate = config.samp_rate // (config.disp_ds * config.save_ds), 
            btype = config.disp_filter_spec['btype'],
            ftype = config.disp_filter_spec['ftype']
        )
        self.disp_queues = disp_queues
        self.running = running

    def _process_usrp(self, data):        
        # Downsample 
        processed = data[::self.config.disp_ds]
        # Filter                                  
        processed, _ = apply_filter(processed, self.disp_filter)
        return processed
    
    def run(self):
        self.logEvent.emit('debug', 'Display started')
        
        disp_data = [None] * len(self.config.disp_channels) 
        idx = 0 
        
        while self.running:
            try:
                for device_type, device_queue in self.disp_queues.items(): 
                    # Load samples
                    samples = device_queue.get() 
                                            
                    if device_type == 'usrp': 
                        processed = self._process_usrp(samples[usrp_channels, :, int(self.config.show_phase)])
                
                bio_channels = self.config.get_display_channels('biopac')
                
                for idx, channel_key in enumerate(self.config.disp_channels):
                    (device_type, channel_idx) = self.config.data_mapping[channel_key]
                    
                    samples = self.disp_queues[device_type].get()  
                    # Process
                    if device_type == 'usrp':  
                        pass 
                    elif device_type == 'biopac': 
                        disp_data[idx] = samples[channel_idx, :]
                
                self.dataReady.emit(np.array(disp_data))
            except queue.Empty:
                self.logEvent.emit('error', 'Queue Empty')
                continue
            except Exception as e:
                self.logEvent.emit('error', f'Display error: {e}')
                continue
                
        self.logEvent.emit('debug', 'Display stopped')
        
    def stop(self):
        self.running = False