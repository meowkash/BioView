# UI for device discovery
import sys 
import time 
from pathlib import Path 

from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTextEdit, QLabel, QStatusBar, QGroupBox, QSpinBox,
        QDoubleSpinBox, QComboBox, QFormLayout
    )
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QGuiApplication, QIcon

from bioview.listeners import ClientHandler

class DeviceControlPanel(QWidget):
    """Device control panel for streaming setup"""
    
    # Signals
    discover_requested = pyqtSignal()
    connect_requested = pyqtSignal(str, dict)  # device_args, config
    disconnect_requested = pyqtSignal()
    start_streaming_requested = pyqtSignal()
    stop_streaming_requested = pyqtSignal()
    configure_requested = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.discovered_devices = []
        self.device_connected = False
        self.streaming_active = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Device discovery and connection
        connection_group = QGroupBox("Device Connection")
        connection_layout = QVBoxLayout(connection_group)
        
        # Discovery
        discovery_layout = QHBoxLayout()
        self.discover_btn = QPushButton("Discover Devices")
        self.discover_btn.clicked.connect(self.discover_requested.emit)
        discovery_layout.addWidget(self.discover_btn)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        discovery_layout.addWidget(self.device_combo)
        discovery_layout.addStretch()
        
        connection_layout.addLayout(discovery_layout)
        
        # Connection buttons
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
        
        # Device configuration
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
        
        # Streaming controls
        streaming_group = QGroupBox("Data Streaming")
        streaming_layout = QVBoxLayout(streaming_group)
        
        stream_button_layout = QHBoxLayout()
        self.start_stream_btn = QPushButton("Start Streaming")
        self.start_stream_btn.clicked.connect(self.start_streaming_requested.emit)
        self.start_stream_btn.setEnabled(False)
        stream_button_layout.addWidget(self.start_stream_btn)
        
        self.stop_stream_btn = QPushButton("Stop Streaming")
        self.stop_stream_btn.clicked.connect(self.stop_streaming_requested.emit)
        self.stop_stream_btn.setEnabled(False)
        stream_button_layout.addWidget(self.stop_stream_btn)
        
        stream_button_layout.addStretch()
        streaming_layout.addLayout(stream_button_layout)
        
        # Streaming status
        self.streaming_status = QLabel("Status: Not streaming")
        streaming_layout.addWidget(self.streaming_status)
        
        layout.addWidget(streaming_group)
        layout.addStretch()
    
    def update_discovered_devices(self, devices):
        """Update device list"""
        self.discovered_devices = devices
        self.device_combo.clear()
        
        if devices:
            for device in devices:
                device_type = device.get('type', 'USRP')
                serial = device.get('serial', 'Unknown')
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
            # Build device args
            device_args = ""
            if 'serial' in current_data:
                device_args = f"serial={current_data['serial']}"
            elif 'addr' in current_data:
                device_args = f"addr={current_data['addr']}"
            
            # Build configuration
            config = {
                'samp_rate': self.sample_rate_spin.value(),
                'carrier_freq': self.center_freq_spin.value(),
                'rx_gain': [self.rx_gain_spin.value()],
                'tx_gain': [self.tx_gain_spin.value()],
                'rx_channels': [0],
                'tx_channels': [0]
            }
            
            self.connect_requested.emit(device_args, config)
    
    def on_configure_clicked(self):
        """Handle configure button click"""
        config = {
            'samp_rate': self.sample_rate_spin.value(),
            'carrier_freq': self.center_freq_spin.value(),
            'rx_gain': [self.rx_gain_spin.value()],
            'tx_gain': [self.tx_gain_spin.value()]
        }
        self.configure_requested.emit(config)
    
    def on_device_connected(self, device_info):
        """Handle device connection"""
        self.device_connected = True
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.configure_btn.setEnabled(True)
        self.start_stream_btn.setEnabled(True)
    
    def on_device_disconnected(self):
        """Handle device disconnection"""
        self.device_connected = False
        self.streaming_active = False
        self.connect_btn.setEnabled(len(self.discovered_devices) > 0)
        self.disconnect_btn.setEnabled(False)
        self.configure_btn.setEnabled(False)
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(False)
        self.streaming_status.setText("Status: Not streaming")
    
    def on_streaming_started(self):
        """Handle streaming start"""
        self.streaming_active = True
        self.start_stream_btn.setEnabled(False)
        self.stop_stream_btn.setEnabled(True)
        self.streaming_status.setText("Status: Streaming active")
    
    def on_streaming_stopped(self):
        """Handle streaming stop"""
        self.streaming_active = False
        self.start_stream_btn.setEnabled(self.device_connected)
        self.stop_stream_btn.setEnabled(False)
        self.streaming_status.setText("Status: Not streaming")
        
class LogDisplayPanel(QWidget):
    """Log display panel"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("System Log")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
    
    def add_log_message(self, level, message):
        """Add log message"""
        timestamp = time.strftime("%H:%M:%S")
        
        color_map = {
            'error': '#ff4444',
            'warning': '#ff8800',
            'info': '#4444ff',
            'debug': '#888888'
        }
        
        color = color_map.get(level.lower(), '#000000')
        formatted_msg = f'<span style="color: {color};">[{timestamp}] {level.upper()}: {message}</span>'
        
        self.log_text.append(formatted_msg)
        
        # Auto-scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear log"""
        self.log_text.clear()

class StatusPanel(QWidget):
    """Status panel"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.server_status = QLabel("Server: Disconnected")
        self.server_status.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.server_status)
        
        layout.addWidget(QLabel("|"))
        
        self.device_status = QLabel("Device: Disconnected")
        layout.addWidget(self.device_status)
        
        layout.addWidget(QLabel("|"))
        
        self.stream_status = QLabel("Stream: Inactive")
        layout.addWidget(self.stream_status)
        
        layout.addStretch()
    
    def update_server_status(self, connected):
        """Update server status"""
        if connected:
            self.server_status.setText("Server: Connected")
            self.server_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.server_status.setText("Server: Disconnected")
            self.server_status.setStyleSheet("color: red; font-weight: bold;")
    
    def update_device_status(self, connected):
        """Update device status"""
        if connected:
            self.device_status.setText("Device: Connected")
            self.device_status.setStyleSheet("color: green;")
        else:
            self.device_status.setText("Device: Disconnected")
            self.device_status.setStyleSheet("color: gray;")
    
    def update_stream_status(self, streaming):
        """Update streaming status"""
        if streaming:
            self.stream_status.setText("Stream: Active")
            self.stream_status.setStyleSheet("color: green;")
        else:
            self.stream_status.setText("Stream: Inactive")
            self.stream_status.setStyleSheet("color: gray;")
            
class DeviceDiscoveryClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_worker = None
        self.init_ui()
        self.setup_client()
    
    def init_ui(self):
        self.setWindowTitle("BioView Device Discovery")
        iconDir = (
            Path(__file__).resolve().parent.parent / "docs" / "assets" / "icon.png"
        )

        self.setWindowIcon(QIcon(str(iconDir)))
        screen = QGuiApplication.primaryScreen().geometry()
        width = screen.width()
        height = screen.height()
        self.setGeometry(
            int(0.4 * width), int(0.3 * height), 600, 600
        )
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        self.control_panel = DeviceControlPanel()
        self.log_panel = LogDisplayPanel()
        main_layout.addWidget(self.control_panel)
        main_layout.addWidget(self.log_panel)
        
        self.status_panel = StatusPanel()
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.status_panel)
        self.setStatusBar(status_bar)
        
        # Connect control panel signals
        self.control_panel.discover_requested.connect(self.discover_devices)
        self.control_panel.connect_requested.connect(self.connect_device)
        self.control_panel.disconnect_requested.connect(self.disconnect_device)
        self.control_panel.start_streaming_requested.connect(self.start_streaming)
        self.control_panel.stop_streaming_requested.connect(self.stop_streaming)
        self.control_panel.configure_requested.connect(self.configure_device)
    
    def setup_client(self):
        """Setup streaming client worker"""
        self.client_worker = ClientHandler()
        
        # Connect signals
        self.client_worker.server_connected.connect(self.on_server_connected)
        self.client_worker.server_disconnected.connect(self.on_server_disconnected)
        self.client_worker.device_connected.connect(self.on_device_connected)
        self.client_worker.device_disconnected.connect(self.on_device_disconnected)
        self.client_worker.streaming_started.connect(self.on_streaming_started)
        self.client_worker.streaming_stopped.connect(self.on_streaming_stopped) 
        self.client_worker.error_occurred.connect(lambda msg: self.log_panel.add_log_message("error", msg))
        self.client_worker.log_message.connect(self.log_panel.add_log_message)
        
        # self.client_worker.data_received.connect(self.on_data_received)
        
        # Start client
        self.client_worker.start_client()
    
    def discover_devices(self):
        """Discover devices"""
        if self.client_worker:
            devices = self.client_worker.discover_devices()
            self.control_panel.update_discovered_devices(devices)
    
    def connect_device(self, device_args, config):
        """Connect to device"""
        if self.client_worker:
            self.client_worker.connect_to_device(device_args, config)
    
    def disconnect_device(self):
        """Disconnect device"""
        if self.client_worker:
            self.client_worker.disconnect_device()
    
    def start_streaming(self):
        """Start data streaming"""
        if self.client_worker:
            self.client_worker.start_streaming()
    
    def stop_streaming(self):
        """Stop data streaming"""
        if self.client_worker:
            self.client_worker.stop_streaming()
    
    def configure_device(self, config):
        """Configure device"""
        if self.client_worker:
            self.client_worker.configure_device(config)
    
    def on_server_connected(self):
        """Handle server connection"""
        self.status_panel.update_server_status(True)
        self.log_panel.add_log_message("info", "Connected to streaming server")
        
        # Auto-ping
        if self.client_worker:
            self.client_worker.ping_server()
    
    def on_server_disconnected(self):
        """Handle server disconnection"""
        self.status_panel.update_server_status(False)
        self.status_panel.update_device_status(False)
        self.status_panel.update_stream_status(False)
        self.control_panel.on_device_disconnected()
    
    def on_device_connected(self, device_info):
        """Handle device connection"""
        self.status_panel.update_device_status(True)
        self.control_panel.on_device_connected(device_info)
        self.log_panel.add_log_message("info", f"Device connected: {device_info}")
    
    def on_device_disconnected(self):
        """Handle device disconnection"""
        self.status_panel.update_device_status(False)
        self.status_panel.update_stream_status(False)
        self.control_panel.on_device_disconnected()
    
    def on_streaming_started(self):
        """Handle streaming start"""
        self.status_panel.update_stream_status(True)
        self.control_panel.on_streaming_started()
    
    def on_streaming_stopped(self):
        """Handle streaming stop"""
        self.status_panel.update_stream_status(False)
        self.control_panel.on_streaming_stopped()
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.client_worker:
            self.client_worker.stop_client()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = DeviceDiscoveryClient()
    window.show()
    
    # Add startup messages
    window.log_panel.add_log_message("info", "Real-time USRP Streaming Application started")
    window.log_panel.add_log_message("info", "Architecture: Server-Client with real-time data streaming")
    window.log_panel.add_log_message("warning", "Make sure streaming_uhd_server.py is running!")
    
    sys.exit(app.exec())
