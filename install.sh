#!/bin/bash

# Automated installation script for Linux, macOS, and Windows
# Handles Python 3.12, UHD installation, and project dependencies

PYTHON_VERSION="python3.12"
VENV_PATH="$HOME/.bioview/venv"
UHD_URL="https://files.ettus.com/binaries/uhd/latest_release/"
PACKAGE_DIR=""

# Helper Functions
log_info() { echo -e "\n\033[1;34m[INFO]\033[0m $1"; }
log_success() { echo -e "\n\033[1;32m[SUCCESS]\033[0m $1"; }
log_warn() { echo -e "\n\033[1;33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\n\033[1;31m[ERROR]\033[0m $1"; exit 1; }
command_exists() { command -v "$1" >/dev/null 2>&1; }

log_info "Starting project installation..."
mkdir -p $HOME/.bioview

# Determine OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

log_info "Detected OS: $OS"

# Install Python 3.12 if not available
log_info "Step 1: Ensuring Python 3.12 is installed..."

if ! command_exists "$PYTHON_VERSION"; then
    log_warn "Python 3.12 not found. Installing..."
    
    if [ "$OS" == "linux" ]; then
        if command_exists "apt"; then
            sudo apt update
            sudo apt install -y software-properties-common
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt update
            sudo apt install -y python3.12 python3.12-venv python3.12-dev
        elif command_exists "dnf"; then
            sudo dnf install -y python3.12 python3.12-devel
        else
            log_error "Unsupported Linux distribution. Please install Python 3.12 manually."
        fi
    elif [ "$OS" == "macos" ]; then
        if ! command_exists "brew"; then
            log_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        brew install python@3.12
        # Create symlink for python3.12 command
        ln -sf $(brew --prefix)/bin/python3.12 /usr/local/bin/python3.12 2>/dev/null || true
    elif [ "$OS" == "windows" ]; then
        log_info "Please install Python 3.12 from Microsoft Store:"
        log_info "1. Open Microsoft Store"
        log_info "2. Search for 'Python 3.12'"
        log_info "3. Install Python 3.12 from Python Software Foundation"
        if command_exists "winget"; then
            log_info "Attempting automatic installation via winget..."
            winget install Python.Python.3.12 || log_warn "Winget installation failed, please install manually."
        fi
        read -p "Press Enter after installing Python 3.12..."
    fi
    
    # Verify installation
    if ! command_exists "$PYTHON_VERSION"; then
        log_error "Python 3.12 installation failed or not in PATH."
    fi
fi

log_success "Python 3.12 is available."

# Install pipx, virtualenv, and poetry
log_info "Step 2: Installing pipx, virtualenv, and poetry..."

if [ "$OS" == "linux" ]; then
    if command_exists "apt"; then
        sudo apt install -y pipx
    elif command_exists "dnf"; then
        sudo dnf install -y pipx
    else
        $PYTHON_VERSION -m pip install --user pipx
    fi
    $PYTHON_VERSION -m pipx ensurepath
    # Refresh PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
elif [ "$OS" == "macos" ]; then
    brew install pipx
    pipx ensurepath
    # Refresh PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
elif [ "$OS" == "windows" ]; then  
    if ! command_exists "scoop"; then
        log_info "Install Scoop first by running in PowerShell as Admin:"
        echo "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
        echo "irm get.scoop.sh | iex"
        read -p "Press Enter after installing Scoop..."
    fi
    scoop install pipx
    pipx ensurepath
    # Refresh PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install tools using pipx
pipx install virtualenv poetry

# Refresh PATH again to ensure virtualenv is available
export PATH="$HOME/.local/bin:$PATH"

# Verify virtualenv is available, fallback to direct pipx execution
if ! command_exists "virtualenv"; then
    VIRTUALENV_CMD="$HOME/.local/bin/virtualenv"
    if [ ! -f "$VIRTUALENV_CMD" ]; then
        log_error "virtualenv not found after installation. PATH may not be updated correctly."
    fi
else
    VIRTUALENV_CMD="virtualenv"
fi

log_success "Tools installed."

# Setup virtualenv
log_info "Step 3: Creating virtual environment..."
$VIRTUALENV_CMD --system-site-packages --python="$PYTHON_VERSION" "$VENV_PATH"

# Activate virtualenv
if [ "$OS" == "windows" ]; then
    source "$VENV_PATH/Scripts/activate"
else
    source "$VENV_PATH/bin/activate"
fi

log_success "Virtual environment created and activated."

# Install project dependencies
log_info "Step 4: Installing project dependencies..."

PROJECT_ROOT=${PACKAGE_DIR:-$(pwd)}
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    log_error "pyproject.toml not found in $PROJECT_ROOT"
fi

(cd "$PROJECT_ROOT" && poetry install)
log_success "Dependencies installed."

# Install UHD
log_info "Step 5: Installing UHD..."

if [ "$OS" == "windows" ]; then
    log_warn "Manual UHD installation required for Windows."
    log_info "Download from: $UHD_URL"
    if command_exists "start"; then
        start $UHD_URL
    fi
    read -p "Press Enter after installing UHD..."
    pip install uhd
elif [ "$OS" == "linux" ]; then
    if command_exists "apt"; then
        sudo apt update
        sudo apt install -y libuhd-dev uhd-host python3-uhd
    elif command_exists "dnf"; then
        sudo dnf install -y uhd uhd-devel
    fi
elif [ "$OS" == "macos" ]; then
    if ! command_exists "port"; then
        log_warn "Install MacPorts from: https://www.macports.org/install.php"
        read -p "Press Enter after installing MacPorts..."
    fi
    sudo port selfupdate
    sudo port install uhd
fi

log_success "UHD installation completed."

# Final instructions
log_success "Installation complete!"
log_info "To activate environment: source \"$VENV_PATH/$([ "$OS" == "windows" ] && echo "Scripts" || echo "bin")/activate\""
log_info "Project directory: $PROJECT_ROOT"