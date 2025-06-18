# 🛠️ Build Instructions

To begin working with **BioView**, you'll need to set up the application in a local, editable environment with all necessary dependencies. The installation process is cross-platform and takes care of Python versioning, virtual environments, and UHD (USRP Hardware Driver) dependencies.

## Prerequisites

* **Git** must be installed and available in your system path.
* On **Windows**, use **Git Bash** or **PowerShell**.
  On **macOS** and **Linux**, use your default terminal.
* **Python 3.12** is required. If not available, the installer will attempt to install it for you.

## Steps

Clone the repository and run the installation script:

```bash
# Clone the repository
git clone https://github.com/meowkash/bioview.git
cd bioview

# Make the script executable (if needed)
chmod +x install.sh

# Run the installation
./install.sh
```

This script performs the following tasks:

1. **Ensures Python 3.12 is installed**:

   * Uses system package managers (APT, DNF, Homebrew, Scoop, etc.) based on your OS.
   * On Windows, will attempt to use `winget` or prompt for manual installation.

2. **Installs tooling**:

   * Installs `pipx`, `virtualenv`, and `poetry` for environment and dependency management.

3. **Installs project dependencies**:
   * Sets up a virtual environment, located at `$HOME/.bioview/venv`, to isolate from system `python`.
   * Uses `poetry install` to install all declared dependencies from `pyproject.toml`.

4. **Installs UHD (USRP Hardware Driver)**:

   * On Linux/macOS: installs via package manager (`apt`, `dnf`, `macports`).
   * On Windows: prompts for manual download and installation via Ettus website ([UHD Downloads](https://files.ettus.com/binaries/uhd/latest_release/)).
   * *For other operating systems, we recommend manually building `uhd` following instructions from Ettus*

After successful installation, activate the virtual environment:

```bash
# macOS/Linux
source ~/.bioview/venv/bin/activate

# Windows
source ~/.bioview/venv/Scripts/activate
```
