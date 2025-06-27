#!/usr/bin/env python3
"""
UHD GUI Client - PyQt6 interface for UHD server
This replicates your bioview UI architecture with the working server-client model
"""

import sys
import socket
import json
import time

from enum import Enum
from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTextEdit, QLabel, QStatusBar, QGroupBox, QSpinBox,
        QDoubleSpinBox, QComboBox, QLineEdit, QFormLayout, QTabWidget,
        QProgressBar, QSplitter
    )
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
    from PyQt6.QtGui import QFont, QTextCursor
except ImportError:
    print("PyQt6 not found. Please install: pip install PyQt6")
    sys.exit(1)

class ConnectionStatus(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"

class CommandType(Enum):
    PING = "ping"
    DISCOVER_DEVICES = "discover_devices"
    CONNECT_DEVICE = "connect_device"
    DISCONNECT_DEVICE = "disconnect_device"
    GET_STATUS = "get_status"
    CONFIGURE_DEVICE = "configure_device"
    SHUTDOWN = "shutdown"

class UHDClientWorker(QThread):
    """Qt thread that manages communication with UHD server"""
    
    # Signals for GUI communication
    server_connected = pyqtSignal()
    server_disconnected = pyqtSignal()
    device_discovered = pyqtSignal(list)  # List of devices
    device_connected = pyqtSignal(dict)   # Device info
    device_disconnected = pyqtSignal()
    configuration_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    log_message = pyqtSignal(str, str)    # level, message
    
    def __init__(self, host='localhost', port=9999):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        
    def start_client(self):
        """Start the client worker"""
        self.running = True
        self.start()
        
    def stop_client(self):
        """Stop the client worker"""
        self.running = False
        self.disconnect_from_server()
        self.quit()
        self.wait()
        
    def run(self):
        """Main worker thread - maintains server connection"""
        self.log_message.emit("info", "Client worker started")
        
        while self.running:
            if not self.connected:
                if self.connect_to_server():
                    self.server_connected.emit()
                else:
                    time.sleep(2)  # Retry connection
                    continue
            
            time.sleep(0.1)  # Main loop delay
            
    def connect_to_server(self):
        """Connect to UHD server"""
        try:
            if self.socket:
                self.socket.close()
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            self.log_message.emit("info", f"Connected to UHD server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.log_message.emit("error", f"Failed to connect to server: {e}")
            return False
    
    def disconnect_from_server(self):
        """Disconnect from server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        if self.connected:
            self.connected = False
            self.server_disconnected.emit()
            self.log_message.emit("info", "Disconnected from UHD server")
    
    def send_command(self, command_type, params=None):
        """Send command to server"""
        if not self.connected:
            self.error_occurred.emit("Not connected to server")
            return None
        
        command = {
            'type': command_type.value,
            'params': params or {}
        }
        
        try:
            # Send command
            command_data = json.dumps(command).encode('utf-8')
            self.socket.send(command_data)
            
            # Receive response
            response_data = self.socket.recv(4096)
            response = json.loads(response_data.decode('utf-8'))
            
            return response
            
        except Exception as e:
            self.error_occurred.emit(f"Communication error: {e}")
            self.disconnect_from_server()
            return None
    
    def ping_server(self):
        """Test server connectivity"""
        self.log_message.emit("debug", "Pinging server...")
        response = self.send_command(CommandType.PING)
        
        if response and response.get('type') == 'success':
            self.log_message.emit("info", "Server ping successful")
            return True
        else:
            self.log_message.emit("error", "Server ping failed")
            return False
    
    def discover_devices(self):
        """Discover USRP devices"""
        self.log_message.emit("info", "Starting device discovery...")
        response = self.send_command(CommandType.DISCOVER_DEVICES)
        
        if response:
            if response.get('type') == 'success':
                step = response.get('step', 'unknown')
                if step == 'discovery':
                    devices = response.get('devices', [])
                    self.log_message.emit("info", f"Found {len(devices)} devices")
                    self.device_discovered.emit(devices)
                else:
                    self.log_message.emit("info", "UHD imported, run discovery again")
            else:
                error_msg = response.get('message', 'Unknown error')
                self.error_occurred.emit(f"Device discovery failed: {error_msg}")
    
    def connect_to_device(self, device_args):
        """Connect to specific device"""
        self.log_message.emit("info", f"Connecting to device: {device_args}")
        response = self.send_command(CommandType.CONNECT_DEVICE, {
            'device_args': device_args
        })
        
        if response:
            if response.get('type') == 'success':
                device_info = response.get('device_info', {})
                self.log_message.emit("info", "Device connected successfully")
                self.device_connected.emit(device_info)
            else:
                error_msg = response.get('message', 'Unknown error')
                self.error_occurred.emit(f"Device connection failed: {error_msg}")
    
    def disconnect_device(self):
        """Disconnect from device"""
        self.log_message.emit("info", "Disconnecting device...")
        response = self.send_command(CommandType.DISCONNECT_DEVICE)
        
        if response and response.get('type') == 'success':
            self.log_message.emit("info", "Device disconnected")
            self.device_disconnected.emit()
    
    def configure_device(self, config):
        """Configure device parameters"""
        self.log_message.emit("info", "Configuring device...")
        response = self.send_command(CommandType.CONFIGURE_DEVICE, config)
        
        if response:
            if response.get('type') == 'success':
                self.log_message.emit("info", "Device configured successfully")
                self.configuration_updated.emit(config)
            else:
                error_msg = response.get('message', 'Unknown error')
                self.error_occurred.emit(f"Configuration failed: {error_msg}")

class DeviceControlPanel(QWidget):
    """Device control panel - similar to your USRP config panel"""
    
    # Signals
    discover_requested = pyqtSignal()
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    configure_requested = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.devices = []
        self.connected_device = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection controls
        connection_group = QGroupBox("Device Connection")
        connection_layout = QVBoxLayout(connection_group)
        
        # Device discovery
        discovery_layout = QHBoxLayout()
        self.discover_btn = QPushButton("Discover Devices")
        self.discover_btn.clicked.connect(self.discover_requested.emit)
        discovery_layout.addWidget(self.discover_btn)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        discovery_layout.addWidget(self.device_combo)
        discovery_layout.addStretch()
        
        connection_layout.addLayout(discovery_layout)
        
        # Connect/Disconnect buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.connect_btn.setEnabled(False)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        button_layout.addStretch()
        connection_layout.addLayout(button_layout)
        
        layout.addWidget(connection_group)
        
        # Configuration controls
        config_group = QGroupBox("Device Configuration")
        config_layout = QFormLayout(config_group)
        
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(1e3, 100e6)
        self.sample_rate_spin.setValue(1e6)
        self.sample_rate_spin.setSuffix(" Hz")
        config_layout.addRow("Sample Rate:", self.sample_rate_spin)
        
        self.center_freq_spin = QDoubleSpinBox()
        self.center_freq_spin.setRange(70e6, 6e9)
        self.center_freq_spin.setValue(2.4e9)
        self.center_freq_spin.setSuffix(" Hz")
        config_layout.addRow("Center Freq:", self.center_freq_spin)
        
        self.rx_gain_spin = QSpinBox()
        self.rx_gain_spin.setRange(0, 76)
        self.rx_gain_spin.setValue(30)
        config_layout.addRow("RX Gain:", self.rx_gain_spin)
        
        self.tx_gain_spin = QSpinBox()
        self.tx_gain_spin.setRange(0, 90)
        self.tx_gain_spin.setValue(10)
        config_layout.addRow("TX Gain:", self.tx_gain_spin)
        
        self.configure_btn = QPushButton("Apply Configuration")
        self.configure_btn.clicked.connect(self.on_configure_clicked)
        self.configure_btn.setEnabled(False)
        config_layout.addRow(self.configure_btn)
        
        layout.addWidget(config_group)
        
        # Device info display
        info_group = QGroupBox("Device Information")
        info_layout = QVBoxLayout(info_group)
        
        self.device_info_text = QTextEdit()
        self.device_info_text.setMaximumHeight(100)
        self.device_info_text.setReadOnly(True)
        info_layout.addWidget(self.device_info_text)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
    
    def update_discovered_devices(self, devices):
        """Update device list from discovery"""
        self.devices = devices
        self.device_combo.clear()
        
        if devices:
            for i, device in enumerate(devices):
                device_type = device.get('type', 'Unknown')
                serial = device.get('serial', 'No Serial')
                display_text = f"{device_type} (S/N: {serial})"
                self.device_combo.addItem(display_text, device)
            
            self.connect_btn.setEnabled(True)
        else:
            self.device_combo.addItem("No devices found")
            self.connect_btn.setEnabled(False)
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        current_data = self.device_combo.currentData()
        if current_data:
            # Build device args string
            device_args = ""
            if 'serial' in current_data:
                device_args = f"serial={current_data['serial']}"
            elif 'addr' in current_data:
                device_args = f"addr={current_data['addr']}"
            
            self.connect_requested.emit(device_args)
    
    def on_configure_clicked(self):
        """Handle configure button click"""
        config = {
            'sample_rate': self.sample_rate_spin.value(),
            'center_freq': self.center_freq_spin.value(),
            'rx_gain': self.rx_gain_spin.value(),
            'tx_gain': self.tx_gain_spin.value()
        }
        self.configure_requested.emit(config)
    
    def on_device_connected(self, device_info):
        """Handle device connection"""
        self.connected_device = device_info
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.configure_btn.setEnabled(True)
        
        # Display device info
        info_text = f"Connected Device:\n"
        info_text += f"Name: {device_info.get('mboard_name', 'Unknown')}\n"
        info_text += f"Boards: {device_info.get('num_mboards', 'Unknown')}"
        self.device_info_text.setPlainText(info_text)
    
    def on_device_disconnected(self):
        """Handle device disconnection"""
        self.connected_device = None
        self.connect_btn.setEnabled(len(self.devices) > 0)
        self.disconnect_btn.setEnabled(False)
        self.configure_btn.setEnabled(False)
        self.device_info_text.clear()

class LogDisplayPanel(QWidget):
    """Log display panel - similar to your log panel"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("System Log")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Clear button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
    
    def add_log_message(self, level, message):
        """Add log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Color coding
        color_map = {
            'error': 'red',
            'warning': 'orange',
            'info': 'blue',
            'debug': 'gray'
        }
        
        color = color_map.get(level.lower(), 'black')
        
        # Format message
        formatted_msg = f'<span style="color: {color};">[{timestamp}] {level.upper()}: {message}</span>'
        
        # Add to log
        self.log_text.append(formatted_msg)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

class ConnectionStatusWidget(QWidget):
    """Connection status indicator"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.server_status = QLabel("Server: Disconnected")
        self.device_status = QLabel("Device: Disconnected")
        
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.server_status)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.device_status)
        layout.addStretch()
    
    def update_server_status(self, connected):
        """Update server connection status"""
        if connected:
            self.server_status.setText("Server: Connected")
            self.server_status.setStyleSheet("color: green;")
        else:
            self.server_status.setText("Server: Disconnected")
            self.server_status.setStyleSheet("color: red;")
    
    def update_device_status(self, connected):
        """Update device connection status"""
        if connected:
            self.device_status.setText("Device: Connected")
            self.device_status.setStyleSheet("color: green;")
        else:
            self.device_status.setText("Device: Disconnected")
            self.device_status.setStyleSheet("color: gray;")

class UHDMainWindow(QMainWindow):
    """Main application window - similar to your ViewerMP"""
    
    def __init__(self):
        super().__init__()
        self.uhd_client = None
        self.init_ui()
        self.setup_client()
        
    def init_ui(self):
        self.setWindowTitle("UHD GUI Client - Server-Client Architecture")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with splitter
        main_layout = QVBoxLayout(central_widget)
        
        # Top section - controls
        top_layout = QHBoxLayout()
        
        # Device control panel
        self.device_panel = DeviceControlPanel()
        top_layout.addWidget(self.device_panel, stretch=1)
        
        # Log display
        self.log_panel = LogDisplayPanel()
        top_layout.addWidget(self.log_panel, stretch=1)
        
        main_layout.addLayout(top_layout)
        
        # Status bar
        self.status_widget = ConnectionStatusWidget()
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.status_widget)
        self.setStatusBar(status_bar)
        
        # Connect device panel signals
        self.device_panel.discover_requested.connect(self.discover_devices)
        self.device_panel.connect_requested.connect(self.connect_device)
        self.device_panel.disconnect_requested.connect(self.disconnect_device)
        self.device_panel.configure_requested.connect(self.configure_device)
        
    def setup_client(self):
        """Setup UHD client worker"""
        self.uhd_client = UHDClientWorker()
        
        # Connect signals
        self.uhd_client.server_connected.connect(self.on_server_connected)
        self.uhd_client.server_disconnected.connect(self.on_server_disconnected)
        self.uhd_client.device_discovered.connect(self.device_panel.update_discovered_devices)
        self.uhd_client.device_connected.connect(self.device_panel.on_device_connected)
        self.uhd_client.device_disconnected.connect(self.device_panel.on_device_disconnected)
        self.uhd_client.error_occurred.connect(self.on_error)
        self.uhd_client.log_message.connect(self.log_panel.add_log_message)
        
        # Start client
        self.uhd_client.start_client()
        
    def discover_devices(self):
        """Discover USRP devices"""
        if self.uhd_client:
            self.uhd_client.discover_devices()
    
    def connect_device(self, device_args):
        """Connect to device"""
        if self.uhd_client:
            self.uhd_client.connect_to_device(device_args)
    
    def disconnect_device(self):
        """Disconnect device"""
        if self.uhd_client:
            self.uhd_client.disconnect_device()
    
    def configure_device(self, config):
        """Configure device"""
        if self.uhd_client:
            self.uhd_client.configure_device(config)
    
    def on_server_connected(self):
        """Handle server connection"""
        self.status_widget.update_server_status(True)
        self.log_panel.add_log_message("info", "Ready for device operations")
        
        # Auto-ping server
        if self.uhd_client:
            self.uhd_client.ping_server()
    
    def on_server_disconnected(self):
        """Handle server disconnection"""
        self.status_widget.update_server_status(False)
        self.status_widget.update_device_status(False)
        self.device_panel.on_device_disconnected()
    
    def on_error(self, error_msg):
        """Handle errors"""
        self.log_panel.add_log_message("error", error_msg)
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.uhd_client:
            self.uhd_client.stop_client()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = UHDMainWindow()
    window.show()
    
    # Add some initial log messages
    window.log_panel.add_log_message("info", "Application started")
    window.log_panel.add_log_message("info", "Attempting to connect to UHD server...")
    window.log_panel.add_log_message("warning", "Make sure uhd_server.py is running!")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()