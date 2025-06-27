# 📥 Installation

This guide walks you through installing the necessary drivers and software dependencies to get started. BioView is cross-platform and designed to run on a wide range of platforms. BioView by itself does not restrict the choice of operating system. However, device manufacturers often do not have cross-platform driver availability so YMMV. The operating systems listed below have been tested to work properly; [contributions](./contributing/feature-request/) are welcome to setup install scripts for other operating systems.

## Supported Operating Systems

BioView has been tested to work well on the following platforms -

* **Windows** (Windows 10 or later)
* **Linux**
  * Ubuntu LTS
  * Debian (stable releases)
  * Other Debian-based distributions (e.g., Linux Mint)

  > ⚠️ *Fedora, RHEL, and derivatives are not officially supported due to missing prebuilt UHD Python bindings. These bindings must be built from source.*
  
  > ⚠️ *Non-LTS versions of Ubuntu are not recommended, as required packages may be missing or incompatible.*
* **macOS**

## Hardware Drivers

### UHD

If you plan to use BioView with a USRP (Universal Software Radio Peripheral) device, the **UHD (USRP Hardware Driver)** must be installed. This section outlines how to install UHD and, if required, the Python bindings necessary for integration with BioView.

#### Installing UHD

Follow the official Ettus Research instructions for your platform:
🔗 [UHD Installation Guide – Ettus Research](https://files.ettus.com/manual/page_build_guide.html)

**On Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install libuhd-dev uhd-host
```

**On Windows:**
Use the precompiled UHD installer from Ettus Research:
🔗 [UHD Windows Downloads](https://files.ettus.com/binaries/)

**On Fedora/RHEL:**
UHD must be built and installed from source. Refer to the Ettus documentation above.

#### UHD Python Bindings (Linux and macOS)

These are required to interface with UHD from within Python:

* **Ubuntu/Debian:**

  ```bash
  sudo apt install python3-uhd
  ```

* **Fedora/RHEL/macOS:**
  You will need to generate and install the Python bindings manually when building UHD from source. The process includes enabling `-DENABLE_PYTHON_API=ON` during the CMake configuration step.

### BIOPAC

You will need to purchase a copy of BioPac Hardware API (BHAPI) and install it using the provided installer. Note that this only works on Windows.

## Dependencies

BioView requires Python 3.12 and a few Python package dependencies. We strongly recommend using a virtual environment to avoid interfering with system-level Python packages.

### Installing Python

* **Windows:**
  Use the **Microsoft Store** to install Python 3.12 (recommended for automatic PATH configuration and updates).

* **Linux:**
  Use your system's package manager to install Python 3.12. For Ubuntu users, if Python 3.12 is not available, consider using `deadsnakes` PPA -

  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install python3.12 python3.12-venv python3.12-dev
  ```

* **macOS:**
  We recommend using ```brew``` to install Python 3.12

### Setting Up the Environment

You can create a virtualenv using either `venv` or `virtualenv`

   ```bash
   python3.12 -m venv bioview-env

   source bioview-env/bin/activate  # Linux/macOS

   bioview-env\Scripts\activate # Windows
   ```

## Installation

BioView can be installed from prebuilt packages available at PyPI

```bash
pip install bioview
```