#!/bin/bash

# This script automates the installation process for the project across Linux, macOS, and Windows.
# It handles UHD installation, Python virtual environment setup, and project dependency installation.

# --- Configuration Variables ---
PYTHON_VERSION="python3.12"
VENV_PATH="$HOME/.zapp/ven"
UHD_URL="https://files.ettus.com/binaries/uhd/latest_release/"
PACKAGE_DIR=""

# --- Helper Functions ---

# Function to display messages
log_info() {
    echo -e "\n\033[1;34m[INFO]\033[0m $1"
}

# Function to display success messages
log_success() {
    echo -e "\n\033[1;32m[SUCCESS]\033[0m $1"
}

# Function to display warning messages
log_warn() {
    echo -e "\n\033[1;33m[WARNING]\033[0m $1"
}

# Function to display error messages and exit
log_error() {
    echo -e "\n\033[1;31m[ERROR]\033[0m $1"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# --- Main Installation Logic ---

log_info "Starting project installation script..."
mkdir $HOME/.zapp # Holds configurations and virtualenv

# --- Determine OS ---
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

log_info "Detected OS: $OS"

# --- Install Python virtualenv and Poetry via pipx ---
log_info "Step 1: Installing pipx, virtualenv, and poetry..."

if [ "$OS" == "linux" ]; then
    if command_exists "apt"; then
        log_info "Installing pipx via apt..."
        sudo apt install -y pipx || log_error "Failed to install pipx via apt."
    elif command_exists "dnf"; then
        log_info "Installing pipx via dnf..."
        sudo dnf install -y pipx || log_error "Failed to install pipx via dnf."
    else
        log_error "Unsupported Linux distribution for pipx installation. Please install pipx manually (e.g., 'python3 -m pip install --user pipx')."
    fi
    # Ensure pipx path is in PATH for current session
    python3 -m pipx ensurepath || log_error "Failed to ensure pipx path."
elif [ "$OS" == "macos" ]; then
    if ! command_exists "brew"; then
        log_warn "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || log_error "Failed to install Homebrew."
        # Add Homebrew to PATH for current session
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    log_info "Installing pipx via Homebrew..."
    brew install pipx || log_error "Failed to install pipx via Homebrew."
    # Ensure pipx path is in PATH for current session
    pipx ensurepath || log_error "Failed to ensure pipx path."
elif [ "$OS" == "windows" ]; then
    if ! command_exists "scoop"; then
        log_warn "Scoop not found. Installing Scoop..."
        # This command needs to be run in PowerShell, not Git Bash.
        # Providing instructions to the user.
        log_info "Please open PowerShell as Administrator and run the following commands to install Scoop:"
        echo "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
        echo "irm get.scoop.sh | iex"
        read -p "Press Enter to continue after you have installed Scoop..."
        if ! command_exists "scoop"; then
            log_error "Scoop still not found after user confirmation. Exiting."
        fi
    fi
    log_info "Installing pipx via Scoop..."
    scoop install pipx || log_error "Failed to install pipx via Scoop."
    # Ensure pipx path is in PATH for current session
    pipx ensurepath || log_error "Failed to ensure pipx path."
else
    log_error "pipx installation is not automated for your operating system ($OS). Please install pipx manually."
fi

log_info "Installing virtualenv and poetry using pipx..."
pipx install virtualenv || log_error "Failed to install virtualenv via pipx."
pipx install poetry || log_error "Failed to install poetry via pipx."
log_success "pipx, virtualenv, and poetry installed."

# --- Setup virtualenv ---
log_info "Step 2: Setting up virtualenv..."

# Check if the specified Python version is available
if ! command_exists "$PYTHON_VERSION"; then
    log_error "$PYTHON_VERSION not found. Please install Python 3.12 and ensure it's in your PATH."
fi

log_info "Creating virtual environment at $VENV_PATH with $PYTHON_VERSION..."
virtualenv --system-site-packages --python="$PYTHON_VERSION" "$VENV_PATH" || log_error "Failed to create virtual environment."
log_success "Virtual environment created at $VENV_PATH."

# --- Install project dependencies with Poetry ---
log_info "Step 3: Installing project dependencies with Poetry..."

# Activate the virtual environment
log_info "Activating virtual environment..."
if [ "$OS" == "windows" ]; then
    # For Git Bash/Cygwin, source the activate script
    source "$VENV_PATH/Scripts/activate" || log_error "Failed to activate virtual environment."
else
    source "$VENV_PATH/bin/activate" || log_error "Failed to activate virtual environment."
fi

if [ -z "$PACKAGE_DIR" ]; then
    log_warn "PACKAGE_DIR is not set. Assuming the script is run from the project root."
    log_info "Poetry will look for pyproject.toml in the current directory."
    # If PACKAGE_DIR is empty, assume current directory is the project root
    PROJECT_ROOT=$(pwd)
else
    log_info "Changing directory to project package: $PACKAGE_DIR"
    if [ ! -d "$PACKAGE_DIR" ]; then
        log_error "Project package directory '$PACKAGE_DIR' not found. Please set PACKAGE_DIR correctly or run the script from the project root."
    fi
    PROJECT_ROOT="$PACKAGE_DIR"
fi

# Change to the project directory and install dependencies
log_info "Navigating to $PROJECT_ROOT and running 'poetry install'..."
(cd "$PROJECT_ROOT" && poetry install) || log_error "Failed to install project dependencies with Poetry. Ensure 'pyproject.toml' is in '$PROJECT_ROOT'."

log_success "Project dependencies installed successfully!"

# --- Installing UHD ---
log_info "Step 4: Installing UHD..."

if [ "$OS" == "windows" ]; then
    log_warn "For Windows, UHD installation is typically a manual process due to GUI installers."
    log_warn "Please download the latest stable UHD installer from Ettus Research and install it manually."
    log_info "Opening the Ettus Research UHD downloads page in your browser..."
    # Attempt to open the URL. 'start' for Windows, 'open' for macOS, 'xdg-open' for Linux.
    if command_exists "start"; then
        start $UHD_URL
    elif command_exists "open"; then
        open $UHD_URL
    elif command_exists "xdg-open"; then
        xdg-open $UHD_URL
    else
        log_warn "Could not open browser automatically. Please visit https://www.ettus.com/support/downloads/uhd-images/ manually."
    fi
    log_info "After installation, please ensure UHD drivers are correctly set up and recognized by your system."
    read -p "Press Enter to continue after you have manually installed UHD..."
    pip install uhd || log_error "Failed to pip install uhd. You may have to manually install uhd later"
elif [ "$OS" == "linux" ]; then
    if command_exists "apt"; then
        log_info "Detected Debian/Ubuntu based system. Installing UHD via apt..."
        sudo apt update || log_error "Failed to update apt packages."
        sudo apt install -y libuhd-dev uhd-host python3-uhd || log_error "Failed to install UHD packages via apt."
    elif command_exists "dnf"; then
        log_info "Detected Fedora/RHEL based system. Installing UHD via dnf..."
        sudo dnf install -y uhd uhd-devel || log_error "Failed to install UHD packages via dnf."
    else
        log_error "Unsupported Linux distribution. Please install UHD manually."
    fi
elif [ "$OS" == "macos" ]; then
    log_info "Detected macOS. Installing UHD via MacPorts..."
    if ! command_exists "port"; then
        log_warn "MacPorts not found. Please install MacPorts first."
        log_info "Instructions: https://www.macports.org/install.php"
        read -p "Press Enter to continue after you have installed MacPorts..."
        if ! command_exists "port"; then
            log_error "MacPorts still not found after user confirmation. Exiting."
        fi
    fi
    sudo port selfupdate || log_error "Failed to update MacPorts."
    sudo port install uhd uhd-devel || log_error "Failed to install UHD packages via MacPorts."
else
    log_error "UHD installation is not automated for your operating system ($OS). Please install UHD manually."
fi
log_success "UHD installation step completed (or manual instructions provided)."

# --- Final Instructions ---
log_info "Installation complete!"
log_info "To activate your virtual environment in the future, run:"
if [ "$OS" == "windows" ]; then
    echo "  source \"$VENV_PATH/Scripts/activate\""
else
    echo "  source \"$VENV_PATH/bin/activate\""
fi
log_info "Then navigate to your project directory (e.g., 'cd $PROJECT_ROOT') to run your project."
log_info "You can deactivate the virtual environment by typing 'deactivate'."