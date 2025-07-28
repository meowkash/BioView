#!/usr/bin/env python3
"""
Streaming UHD Server - Handles UHD operations with real-time data streaming
Integrates your existing USRP backend (ProcessWorker, ReceiveWorker, etc.) with server-client model
"""

import socket
import json
import time
import os
import sys
import threading
import traceback
import queue
import numpy as np
import struct
from enum import Enum
import uhd 
from bioview.device import discover_devices

print(sys.modules.keys())

# Windows DLL setup
if sys.platform == "win32":
    print("Setting up Windows DLL paths...")
    uhd_paths = [
        r"C:\Program Files\UHD\bin",
        r"C:\Program Files (x86)\UHD\bin", 
        r"C:\local\uhd\bin"
    ]
    
    for path in uhd_paths:
        if os.path.exists(path):
            try:
                os.add_dll_directory(path)
                print(f"✓ Added UHD DLL path: {path}")
                break
            except Exception as e:
                print(f"✗ Failed to add DLL path {path}: {e}")

class CommandType(Enum):
    PING = "ping"
    DISCOVER_DEVICES = "discover_device"
    CONNECT_DEVICE = "connect_device"
    DISCONNECT_DEVICE = "disconnect_device"
    CONFIGURE_DEVICE = "configure_device"
    START_STREAMING = "start_streaming"
    STOP_STREAMING = "stop_streaming"
    GET_STATUS = "get_status"
    SHUTDOWN = "shutdown"

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    STREAM_DATA = "stream_data"

class StreamingDataServer:
    """Server that handles both control commands and real-time data streaming"""
    
    def __init__(self, control_host='localhost', control_port=9999, data_port=9998):
        self.control_host = control_host
        self.control_port = control_port
        self.data_port = data_port
        
        # Sockets
        self.control_socket = None
        self.data_socket = None
        
        # Server state
        self.running = False
        self.uhd_imported = False
        self.uhd = None
        
        # USRP components (using your existing classes)
        self.usrp_device = None
        self.device_config = None
        
        # Data streaming
        self.streaming = False
        self.data_clients = []  # List of connected data clients
        self.data_lock = threading.Lock()
        
    def start(self):
        """Start both control and data servers"""
        print(f"Starting Streaming UHD Server...")
        print(f"Control port: {self.control_port}")
        print(f"Data streaming port: {self.data_port}")
        
        try:
            # Start control server
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.control_socket.bind((self.control_host, self.control_port))
            self.control_socket.listen(5)
            
            # Start data server
            self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.data_socket.bind((self.control_host, self.data_port))
            self.data_socket.listen(10)  # More clients for data
            
            self.running = True
            
            print(f"✓ Control server listening on {self.control_host}:{self.control_port}")
            print(f"✓ Data server listening on {self.control_host}:{self.data_port}")
            
            # Start server threads
            control_thread = threading.Thread(target=self.run_control_server, daemon=True)
            data_thread = threading.Thread(target=self.run_data_server, daemon=True)
            
            control_thread.start()
            data_thread.start()
            
            # Keep main thread alive
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server"""
        print("Stopping Streaming UHD Server...")
        self.running = False
        
        # Stop streaming
        self.stop_data_streaming()
        
        # Close sockets
        if self.control_socket:
            self.control_socket.close()
        if self.data_socket:
            self.data_socket.close()
            
        print("Server stopped")
    
    def run_control_server(self):
        """Run control command server"""
        while self.running:
            try:
                client_socket, address = self.control_socket.accept()
                print(f"Control client connected from {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_control_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Error accepting control connection: {e}")
    
    def run_data_server(self):
        """Run data streaming server"""
        while self.running:
            try:
                client_socket, address = self.data_socket.accept()
                print(f"Data client connected from {address}")
                
                with self.data_lock:
                    self.data_clients.append(client_socket)
                
                # Handle client disconnect
                def monitor_client(sock):
                    try:
                        while self.running:
                            # Send keepalive
                            sock.send(b'')
                            time.sleep(1)
                    except:
                        with self.data_lock:
                            if sock in self.data_clients:
                                self.data_clients.remove(sock)
                        sock.close()
                        print(f"Data client {address} disconnected")
                
                threading.Thread(target=monitor_client, args=(client_socket,), daemon=True).start()
                
            except Exception as e:
                if self.running:
                    print(f"Error accepting data connection: {e}")
    
    def handle_control_client(self, client_socket):
        """Handle control client"""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    command = json.loads(data.decode('utf-8'))
                    response = self.process_command(command)
                    
                    response_data = json.dumps(response).encode('utf-8')
                    client_socket.send(response_data)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        'type': ResponseType.ERROR.value,
                        'message': f"Invalid JSON: {e}"
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            print(f"Control client error: {e}")
        finally:
            client_socket.close()
    
    def process_command(self, command):
        """Process control commands"""
        cmd_type = command.get('type')
        params = command.get('params', {})
        
        # Debug logging
        print(f"📨 Received command: {json.dumps(command, indent=2)}")
        print(f"🔍 Command type: '{cmd_type}' (type: {type(cmd_type)})")
        print(f"📋 Available commands: {[cmd.value for cmd in CommandType]}")
        
        try:
            if cmd_type == CommandType.PING.value:
                return self.handle_ping()
            elif cmd_type == CommandType.DISCOVER_DEVICES.value:
                return self.handle_discover_devices()
            elif cmd_type == CommandType.CONNECT_DEVICE.value:
                return self.handle_connect_device(params)
            elif cmd_type == CommandType.DISCONNECT_DEVICE.value:
                return self.handle_disconnect_device()
            elif cmd_type == CommandType.CONFIGURE_DEVICE.value:
                return self.handle_configure_device(params)
            elif cmd_type == CommandType.START_STREAMING.value:
                return self.handle_start_streaming(params)
            elif cmd_type == CommandType.STOP_STREAMING.value:
                return self.handle_stop_streaming()
            elif cmd_type == CommandType.GET_STATUS.value:
                return self.handle_get_status()
            elif cmd_type == CommandType.SHUTDOWN.value:
                return self.handle_shutdown()
            else:
                return {
                    'type': ResponseType.ERROR.value,
                    'message': f"Unknown command: '{cmd_type}'",
                    'received_command': command,
                    'available_commands': [cmd.value for cmd in CommandType]
                }
                
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f"Command processing error: {e}",
                'traceback': traceback.format_exc()
            }
    
    def handle_ping(self):
        """Handle ping command"""
        return {
            'type': ResponseType.SUCCESS.value,
            'message': 'pong',
            'server_info': {
                'server_type': 'streaming_uhd',
                'uhd_imported': self.uhd_imported,
                'device_connected': self.usrp_device is not None,
                'streaming': self.streaming,
                'data_clients': len(self.data_clients)
            }
        }
    
    def handle_discover_devices(self):
        """Handle device discovery"""
        print("🔍 Starting device discovery...")
        
        if not self.uhd_imported:
            try:
                print("📦 Importing UHD...")
                import uhd
                self.uhd = uhd
                self.uhd_imported = True
                print("✓ UHD imported successfully")
            except Exception as e:
                return {
                    'type': ResponseType.ERROR.value,
                    'message': f'UHD import failed: {e}'
                }
        
        try:
            print("🔍 Calling uhd.find()...")
            devices = self.uhd.find("")
            
            device_list = []
            for device in devices:
                device_dict = dict(device)
                device_list.append(device_dict)
            
            print(f"✓ Found {len(devices)} devices")
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': f'Found {len(devices)} devices',
                'devices': device_list
            }
            
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Device discovery failed: {e}',
                'traceback': traceback.format_exc()
            }
    
    def handle_connect_device(self, params):
        """Handle device connection using your existing architecture"""
        device_args = params.get('device_args', '')
        config_params = params.get('config', {})
        
        print(f"🔌 Connecting to device: {device_args}")
        
        try:
            # Create a mock configuration (you'd replace this with your actual config)
            from types import SimpleNamespace
            
            # Create minimal config that matches your UsrpConfiguration interface
            config = SimpleNamespace()
            config.device_name = device_args
            config.rx_subdev = config_params.get('rx_subdev', 'A:A')
            config.tx_subdev = config_params.get('tx_subdev', 'A:A')
            config.rx_channels = config_params.get('rx_channels', [0])
            config.tx_channels = config_params.get('tx_channels', [0])
            config.samp_rate = config_params.get('samp_rate', 1e6)
            config.carrier_freq = config_params.get('carrier_freq', 2.4e9)
            config.rx_gain = config_params.get('rx_gain', [30])
            config.tx_gain = config_params.get('tx_gain', [10])
            config.clock = config_params.get('clock', 'internal')
            config.pps = config_params.get('pps', 'internal')
            config.cpu_format = 'fc32'
            config.wire_format = 'sc16'
            
            # Add methods that your code expects
            def get_param(key, default=None):
                return getattr(config, key, default)
            config.get_param = get_param
            
            # Store config for later use
            self.device_config = config
            
            # Import and create your existing USRP components
            # NOTE: You'll need to adapt the imports based on your actual module structure
            from bioview.device.usrp.device import UsrpDeviceWrapper  # Adjust import path
            
            # Create device wrapper using your existing code
            self.usrp_device = UsrpDeviceWrapper(
                device_name="server_device",
                config=config
            )
            
            # Set up callbacks for data streaming
            self.usrp_device.log_event = self._log_callback
            self.usrp_device.connection_state_changed = self._connection_callback
            
            # Connect the device
            self.usrp_device.connect()
            
            # Wait for connection to complete
            # In your real implementation, you'd handle this with proper async callbacks
            time.sleep(2)
            
            if hasattr(self.usrp_device, 'handler') and self.usrp_device.handler:
                device_info = {
                    'connected': True,
                    'device_args': device_args,
                    'config': config_params
                }
                
                print("✓ Device connected successfully")
                return {
                    'type': ResponseType.SUCCESS.value,
                    'message': 'Device connected successfully',
                    'device_info': device_info
                }
            else:
                return {
                    'type': ResponseType.ERROR.value,
                    'message': 'Device connection failed'
                }
                
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Device connection failed: {e}',
                'traceback': traceback.format_exc()
            }
    
    def handle_start_streaming(self, params):
        """Start real-time data streaming"""
        if not self.usrp_device or not hasattr(self.usrp_device, 'handler'):
            return {
                'type': ResponseType.ERROR.value,
                'message': 'No device connected'
            }
        
        try:
            print("🚀 Starting data streaming...")
            
            # Start your existing receive/transmit workers
            self.usrp_device.run()
            
            # Start data streaming thread
            self.streaming = True
            streaming_thread = threading.Thread(target=self._stream_data, daemon=True)
            streaming_thread.start()
            
            print("✓ Data streaming started")
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Data streaming started'
            }
            
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Failed to start streaming: {e}',
                'traceback': traceback.format_exc()
            }
    
    def handle_stop_streaming(self):
        """Stop data streaming"""
        try:
            self.stop_data_streaming()
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Data streaming stopped'
            }
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Failed to stop streaming: {e}'
            }
    
    def stop_data_streaming(self):
        """Stop data streaming"""
        if self.streaming:
            print("🛑 Stopping data streaming...")
            self.streaming = False
            
            if self.usrp_device:
                self.usrp_device.stop()
    
    def _stream_data(self):
        """Stream real-time data to connected clients"""
        print("📡 Data streaming thread started")
        
        # This is where you'd integrate with your ProcessWorker output
        # For now, simulate data streaming
        
        while self.streaming and self.running:
            try:
                # Get processed data from your ProcessWorker
                # In your real implementation, you'd get this from the ProcessWorker's output queue
                
                # Simulate getting data (replace with actual data from ProcessWorker)
                if hasattr(self.usrp_device, 'rx_queue'):
                    try:
                        # Get raw data from receive worker
                        raw_data = self.usrp_device.rx_queue.get(timeout=0.1)
                        
                        # Process data (you'd use your ProcessWorker here)
                        processed_data = self._simulate_processing(raw_data)
                        
                        # Send to connected clients
                        self._send_data_to_clients(processed_data)
                        
                    except queue.Empty:
                        continue
                else:
                    # Simulate data for testing
                    time.sleep(0.01)  # 100 Hz update rate
                    sim_data = np.random.random((2, 100)).astype(np.float32)
                    self._send_data_to_clients(sim_data)
                    
            except Exception as e:
                print(f"Streaming error: {e}")
                time.sleep(0.1)
        
        print("📡 Data streaming thread stopped")
    
    def _simulate_processing(self, raw_data):
        """Simulate your ProcessWorker output (replace with actual ProcessWorker integration)"""
        # This is a placeholder - you'd integrate your actual ProcessWorker here
        if isinstance(raw_data, np.ndarray):
            # Convert complex data to magnitude for plotting
            if raw_data.dtype == np.complex64:
                processed = np.abs(raw_data)
            else:
                processed = raw_data
            
            # Downsample for display
            if processed.shape[-1] > 1000:
                step = processed.shape[-1] // 1000
                processed = processed[..., ::step]
            
            return processed.astype(np.float32)
        else:
            # Fallback simulation
            return np.random.random((2, 100)).astype(np.float32)
    
    def _send_data_to_clients(self, data):
        """Send processed data to connected clients"""
        if len(self.data_clients) == 0:
            return
        
        try:
            # Serialize data efficiently
            data_bytes = self._serialize_data(data)
            
            # Send to all connected clients
            with self.data_lock:
                disconnected_clients = []
                
                for client in self.data_clients:
                    try:
                        # Send data length first, then data
                        length_header = struct.pack('!I', len(data_bytes))
                        client.send(length_header + data_bytes)
                    except:
                        disconnected_clients.append(client)
                
                # Remove disconnected clients
                for client in disconnected_clients:
                    self.data_clients.remove(client)
                    client.close()
                    
        except Exception as e:
            print(f"Error sending data to clients: {e}")
    
    def _serialize_data(self, data):
        """Efficiently serialize numpy data for transmission"""
        # Create header with metadata
        header = {
            'shape': data.shape,
            'dtype': str(data.dtype),
            'timestamp': time.time()
        }
        
        # Convert to bytes
        header_bytes = json.dumps(header).encode('utf-8')
        header_length = struct.pack('!I', len(header_bytes))
        data_bytes = data.tobytes()
        
        return header_length + header_bytes + data_bytes
    
    def _log_callback(self, level, message):
        """Callback for log events from USRP components"""
        print(f"[{level.upper()}] {message}")
    
    def _connection_callback(self, status):
        """Callback for connection state changes"""
        print(f"Connection status: {status}")
    
    def handle_disconnect_device(self):
        """Handle device disconnection"""
        try:
            self.stop_data_streaming()
            
            if self.usrp_device:
                self.usrp_device.stop()
                self.usrp_device = None
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Device disconnected'
            }
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Disconnect failed: {e}'
            }
    
    def handle_configure_device(self, params):
        """Handle device configuration"""
        if not self.usrp_device:
            return {
                'type': ResponseType.ERROR.value,
                'message': 'No device connected'
            }
        
        try:
            # Update configuration
            if self.device_config:
                for key, value in params.items():
                    if hasattr(self.device_config, key):
                        setattr(self.device_config, key, value)
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Device configured',
                'config': params
            }
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Configuration failed: {e}'
            }
    
    def handle_get_status(self):
        """Get current status"""
        return {
            'type': ResponseType.SUCCESS.value,
            'message': 'Status retrieved',
            'status': {
                'uhd_imported': self.uhd_imported,
                'device_connected': self.usrp_device is not None,
                'streaming': self.streaming,
                'data_clients': len(self.data_clients)
            }
        }
    
    def handle_shutdown(self):
        """Handle server shutdown"""
        def stop_server():
            time.sleep(0.5)
            self.stop()
        
        threading.Thread(target=stop_server, daemon=True).start()
        
        return {
            'type': ResponseType.SUCCESS.value,
            'message': 'Server shutting down'
        }

def main():
    print("=" * 60)
    print("Streaming UHD Server - Real-time Data Support")
    print("Integrates with existing USRP backend architecture")
    print("=" * 60)
    
    server = StreamingDataServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
    except Exception as e:
        print(f"Server error: {e}")
        traceback.print_exc()
    finally:
        server.stop()

if __name__ == "__main__":
    main()