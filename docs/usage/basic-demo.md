# Basic Demo

In order to run an experiment using bioview, you need to create an executable file similar to the example below -

```Python
import sys 
import faulthandler

from bioview.app import Viewer
from bioview.types import UsrpConfiguration, ExperimentConfiguration, BiopacConfiguration

from PyQt6.QtWidgets import QApplication

# Usually a good idea to have a crash log 
faulthandler.enable(open('crash.log', 'w'), all_threads=True)

# Experiment variables 
exp_config = ExperimentConfiguration(
    save_dir = '/home',
    file_name = 'example', 
    save_ds = 100,    
    disp_ds = 10, 
    disp_filter_spec = {
        'bounds': 10,
        'btype': 'low',
        'ftype': 'butter' 
    },
    disp_channels = ['Tx1Rx1', 'Tx2Rx2', 'Tx1Rx2', 'Tx2Rx1'],
)

# USRP variables 
usrp = UsrpConfiguration(
    device_name = 'MyB210_4', 
    if_freq = [100e3, 110e3],
    if_bandwidth = 5e3, 
    rx_gain = [25, 35], 
    tx_gain = [43, 37], 
    samp_rate = 1e6, 
    carrier_freq = 9e8,
)

# Biopac Control
bio = BiopacConfiguration(
    device_name = 'MyBIOPAC', 
    channels = [1, 1, 0, 0]
)

# Run application
app = QApplication(sys.argv)

window = Viewer(exp_config=exp_config,
                usrp_config=[usrp], 
                bio_config=bio)
window.show()

sys.exit(app.exec())
```