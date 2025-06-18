# BIOPAC

BioView is able to acquire data from a wide variety of BIOPAC devices, such as MP36, MP150, MP160, through its `BiopacDevice` backend. There are, however, a few considerations -

* You must have a legally purchased copy of the **BIOPAC Hardware API (BHAPI)** which provides helper files for BioView to use. BioView will never provide these files since they are the intellectual property of BIOPAC Inc.
* While BioView is platform agnostic, **BHAPI** is restricted to Windows only. As such, this functionality is limited to Windows only.

## Prerequisites

* A compatible BIOPAC data acquisition unit (e.g., MP36, MP150, MP160)
* Windows OS
* `mpdev.dll` (BIOPAC Hardware API library)

Ensure `mpdev.dll` is discoverable, either by being in your working folder, in `$PATH`, in the OS install drive, or in a configuration path provided manually.

## BIOPAC Hardware API

![BHAPI Illustration Provided by BIOPAC Inc](https://www.biopac.com/wp-content/uploads/bhapi_with.gif)

The provided `mpdev.dll` file allows us to connect to devices as well as stream data across a variety of configurations. Some of the most crucial steps for our use case are described below.

### Available Functionality

| Function              | Description                                  |
| --------------------- | -------------------------------------------- |
| `connectMPDev`        | Establish device connection (USB or UDP)     |
| `setAcqChannels`      | Activate specific analog input channels      |
| `setSampleRate`       | Define sampling interval                     |
| `startAcquisition`    | Begin live data collection                   |
| `getMostRecentSample` | Retrieve most recent sample (with timestamp) |

### Device Connection

The `connectMPDev` function uses parameters that define the device and communication type:

```c
int connectMPDev(int deviceCode, int connectionType, const char* portName);
```

#### Device Codes

Common `deviceCode` values include:

* `103` for **MP36** / MP36R
* `150` for **MP150**
* `160` for **MP160**

Refer to BIOPAC documentation for additional codes if you're using other models.

#### Connection Types

`connectionType` determines the transport interface:

* **10**: USB (automatic detection)
* **20**: Ethernet/UDP (typically used with MP150/160)

#### Port Types

The `portName` argument supports:

* `"auto"` for auto-discovery (USB only)
* A specific COM port (e.g., `"COM3"`)
* A UDP IP address (e.g., `"169.254.111.111"` for MP150/160)

### Additional Notes

* MP150/160 devices can use **Ethernet (UDP)** connections with the IP `169.254.x.x`
* Always call `stopAcquisition` and `disconnectMPDev` during cleanup
* Ensure firewall/driver permissions are granted for device access
* Ensure architecture compatibility (32-bit vs 64-bit) between the DLL and your Python interpreter.

For additional functionality (digital outputs, electrode detection, calibration), consult the official BIOPAC Hardware API reference.

## Usage Examples

Here's an example from BioView on how to connect to a supported device using BHAPI

```python
from ctypes import c_int, c_double, byref

self.biopac = load_mpdev_dll(self.config.mpdev_path)
if self.biopac is None:
    self.logEvent.emit(
        "mpdev.dll not found. Ensure it is in PATH or configure 'mpdev_path'."
    )
    return

# Example: MP36 via USB
device_code = c_int(103)
connection_type = c_int(10)
port_name = b"auto"

wrap_result_code(
    self.biopac.connectMPDev(device_code, connection_type, port_name),
    "Initialization"
)
```

*Note: Use values relevant to your setup. This example uses an MP36 over USB.*

### Configuration

#### Modify Acquisition Channels

Instead of acquiring data over all channels in your device, you can specify which channels to use for reducing system load

```python
channels_array = (c_int * 16)(*self.config.get_channels())
wrap_result_code(
    self.biopac.setAcqChannels(byref(channels_array)), "Set Channels"
)
```

#### Modify Sample Rate

```python
wrap_result_code(
    self.biopac.setSampleRate(c_double(self.config.get_samp_time())),
    "Set Sample Rate"
)
```

### Data Acquisition

```python
wrap_result_code(self.biopac.startAcquisition())

num_channels = len(self.config.channels)
data_buffer = (c_double * (num_channels + 1))()  # includes timestamp

while self.running:
    if wrap_result_code(self.biopac.getMostRecentSample(byref(data_buffer))):
        sample = [data_buffer[i] for i in range(num_channels + 1)]
        self.rx_queue.put(sample)
```

### Error Handling

In general, BIOPAC devices communicate an error state by sending the status code `0` as a result of a command. In order to bring this in line with Python's error handling, BioView wraps all device calls to catch and raise errors in a Pythonic fashion.

```python
def wrap_result_code(result: int, context: str = ""):
    if result != 0:
        raise RuntimeError(f"BIOPAC Error ({context}): Code {result}")
    return True
```

*As a general rule of thumb, log or display errors to improve debugging visibility.*