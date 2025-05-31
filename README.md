# BioView

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

BioView is a versatile, extensible, and performant cross-platform app for biomedical and human-computer interface instrumentation control, including Ettus USRPs and BIOPAC devices.

## Features

* **Real-time USRP Control:** Interface with Ettus USRP devices for high-throughput transceiving
* **BIOPAC Integration:** Synchronized physiological data collection alongside RF measurements
  * *You must already possess a copy of the BIOPAC Hardware API purchased from BIOPAC Systems Inc. for this to work*
* **Live Data Visualization:** Sensor data is visualized in real-time
* **Synchronized Data Acquisition:** Save synchronized hardware data streams with precise timing control
* **Experiment Management:** Configure and control experimental routines and settings
* **Event Annotation:** Mark and annotate events during data collection
* **Multi-format Data Storage:** Flexible data saving with multiple format support

## Installation

### Supported Operating Systems

The project is supported on the following operating systems -

* **Windows**
* **macOS**
* **Linux:** Ubuntu, Debian, Fedora, and RHEL

### Instructions

The installation requires you to have ```git``` installed in your system. In a terminal window, follow the steps listed below. *On Windows, use Git Bash for this. On Linux and macOS, use the native terminal app.*

```bash
# Clone repository 
cd ~ 
git clone https://github.com/meowkash/bioview.git 

# Run installer script
cd bioview
chmod +x install.sh
./install.sh 
```

## Usage

In order to run an experiment using bioview, you need to create an executable file similar to the example below -

```Python
import sys 
import faulthandler

from bioview.app import Viewer
from bioview.constants import UsrpConfiguration, ExperimentConfiguration

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

app = QApplication(sys.argv)

window = Viewer(exp_config=exp_config,
                    usrp_config=[usrp])
window.show()

sys.exit(app.exec())
```

## Performance Considerations

* Real-time data acquisition requires sufficient system resources
* Large data streams may require SSD storage for optimal performance
* Memory usage scales with buffer sizes and visualization complexity. Visualization is kept efficient by only updating data streams for source that are actually visible
* Spikes may occur in the data if receive buffer is kept low in size due to filtering edge effects
* B210 devices work poorly with default frame sizes, which is why default receive frame size has been kept at 1024

## Troubleshooting

Common issues and solutions:

1. **USRP Device Not Detected**: Verify hardware connections and driver installation
2. **High CPU Usage**: Adjust buffer sizes and visualization update rates
3. **Data Loss**: Check storage write speeds and available disk space
4. **Synchronization Issues**: Verify system clock accuracy and BIOPAC timing

Check `crash.log` for detailed error information and diagnostic data.

## Development

### Structure

```bash
bioview/
├── app.py              # Main application
├── usrp/               # USRP core functionality
├── common/             # Common functionality
├── components/         # GUI components
├── biopac/             # BIOPAC integration
├── utils/              # Utility functions
├── types/              # Custom data-types 
└── constants/          # App-specific constants
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes and run tests
4. Submit a pull request

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the LICENSE file for the complete license text.
