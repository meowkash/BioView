# Contributing

## 🧱 Code Style and Architecture

The BioView codebase is structured with clarity and modularity in mind. We follow a broad **Model–View–Controller (MVC)** paradigm to ensure separation of concerns and hardware-independence.

### Project Structure

```bash
bioview/
├── app.py              # Main entry point 
├── device/             # Backend 
    ├── common/             # Shared helpers and common tooling
    ├── <device_name>/      # Device-specific implementation
├── constants/          # Application-wide constants
├── types/              # Data models and type definitions
├── ui/                 # Frontend
└── utils/              # General-purpose utilities
```

### Architectural Philosophy

#### Types and Data Models

All generic data structures (e.g., `Device`, `Configuration`, etc.) should be defined in the `types/` directory. This allows clean reuse across the app.

#### Domain-Specific Implementations

Specific functionality (e.g., USRP-specific subclasses) should be implemented in their respective module folders (e.g., `usrp/`, `biopac/`). This keeps generic definitions clean and backend-specific logic isolated.

#### MVC Paradigm

Broadly speaking, BioView aligns with the [MVC architecture](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller). The base implementation is structured as follows -

* **Model**: Device specific backends (such as for USRP, BIOPAC, etc) with a common API in  `device/`
* **View**: GUI components in the `ui/` directory
* **Controller**: `app.py` as a fairly non-opinionated controller

We implement this structure to encourage higher code quality and would urge you to stick with the same paradigm so that BioView remains - 

* Easy to extend for new hardware backends
* Maintainable and testable
* Decoupled between frontend (UI) and backend (hardware/control logic)

### Style Guidelines

* Follow [PEP8](https://peps.python.org/pep-0008/) conventions unless explicitly overridden.
* Use type annotations and docstrings for all public functions and classes.
* Avoid placing business logic inside UI components—keep the UI declarative and reactive.
* Organize code into appropriate modules as outlined above, and prefer modular, composable functions and classes.

### Pre-formatters

As the codebase scales, enforcing good coding practices becomes a challenge. We simplify this by making use of [`precommit`](https://pre-commit.com) which uses the following hooks to validate code before it gets committed -

* [`black`](https://black.readthedocs.io/en/stable/) is used for code formatting.
* [`flake8`](https://flake8.pycqa.org/en/latest/) is used to enforce PEP8 compliance.
* [`isort`](https://pycqa.github.io/isort/) helps clean up messy import statements into a cohesive structure.

Please do not try to force through commits by skipping `pre-commit` checks as that will only make the codebase unmaintainable over time. 

## 🛠️ Build Instructions

To begin working with **BioView**, you'll need to set up the application in a local, editable environment with all necessary dependencies. The installation process is cross-platform and takes care of Python versioning, virtual environments, and UHD (USRP Hardware Driver) dependencies.

### Prerequisites

* **Git** must be installed and available in your system path.
* On **Windows**, use **Git Bash** or **PowerShell**.
  On **macOS** and **Linux**, use your default terminal.
* **Python 3.12** is required. If not available, the installer will attempt to install it for you.

### Setup Steps

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

---
