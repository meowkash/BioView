#!/usr/bin/env python3
"""
UHD Server - Standalone process that handles all UHD operations
Run this separately to debug UHD issues in isolation
"""

import socket
import json
import time
import os
import sys
import threading
import traceback
from enum import Enum

# Windows DLL setup - MUST be before importing uhd
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
                print(f"✓ Added DLL path: {path}")
                break
            except Exception as e:
                print(f"✗ Failed to add DLL path {path}: {e}")

class CommandType(Enum):
    PING = "ping"
    DISCOVER_DEVICES = "discover_devices"
    CONNECT_DEVICE = "connect_device"
    DISCONNECT_DEVICE = "disconnect_device"
    GET_STATUS = "get_status"
    CONFIGURE_DEVICE = "configure_device"
    SHUTDOWN = "shutdown"

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    DEBUG = "debug"

class UHDServer:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.uhd_imported = False
        self.uhd = None
        self.usrp = None
        self.tx_streamer = None
        self.rx_streamer = None
        self.device_info = None
        
    def start(self):
        """Start the UHD server"""
        print(f"Starting UHD Server on {self.host}:{self.port}")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"✓ Server listening on {self.host}:{self.port}")
            print("Waiting for clients...")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"Client connected from {address}")
                    
                    # Handle client in a new thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}")
                        
        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server"""
        print("Stopping UHD Server...")
        self.running = False
        if self.socket:
            self.socket.close()
        print("Server stopped")
    
    def handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            while self.running:
                # Receive command
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    command = json.loads(data.decode('utf-8'))
                    print(f"Received command: {command.get('type', 'unknown')}")
                    
                    # Process command
                    response = self.process_command(command)
                    
                    # Send response
                    response_data = json.dumps(response).encode('utf-8')
                    client_socket.send(response_data)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        'type': ResponseType.ERROR.value,
                        'message': f"Invalid JSON: {e}"
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            client_socket.close()
            print("Client disconnected")
    
    def process_command(self, command):
        """Process incoming commands"""
        cmd_type = command.get('type')
        
        try:
            if cmd_type == CommandType.PING.value:
                return self.handle_ping()
            elif cmd_type == CommandType.DISCOVER_DEVICES.value:
                return self.handle_discover_devices()
            elif cmd_type == CommandType.CONNECT_DEVICE.value:
                return self.handle_connect_device(command.get('params', {}))
            elif cmd_type == CommandType.DISCONNECT_DEVICE.value:
                return self.handle_disconnect_device()
            elif cmd_type == CommandType.GET_STATUS.value:
                return self.handle_get_status()
            elif cmd_type == CommandType.CONFIGURE_DEVICE.value:
                return self.handle_configure_device(command.get('params', {}))
            elif cmd_type == CommandType.SHUTDOWN.value:
                return self.handle_shutdown()
            else:
                return {
                    'type': ResponseType.ERROR.value,
                    'message': f"Unknown command: {cmd_type}"
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
                'python_version': sys.version,
                'platform': sys.platform,
                'uhd_imported': self.uhd_imported
            }
        }
    
    def handle_discover_devices(self):
        """Handle device discovery - THIS IS WHERE CRASHES HAPPEN"""
        print("🔍 Starting device discovery...")
        
        # Step 1: Try to import UHD
        if not self.uhd_imported:
            try:
                print("📦 Importing UHD...")
                import uhd
                self.uhd = uhd
                self.uhd_imported = True
                print("✓ UHD imported successfully")
                
                return {
                    'type': ResponseType.SUCCESS.value,
                    'message': 'UHD imported successfully',
                    'step': 'import'
                }
                
            except Exception as e:
                print(f"✗ UHD import failed: {e}")
                return {
                    'type': ResponseType.ERROR.value,
                    'message': f'UHD import failed: {e}',
                    'step': 'import'
                }
        
        # Step 2: Try device discovery
        try:
            print("🔍 Calling uhd.find()...")
            print("⚠️  This is where crashes typically happen...")
            
            # The problematic call
            devices = self.uhd.find("")
            
            print(f"✓ uhd.find() succeeded! Found {len(devices)} devices")
            
            device_list = []
            for i, device in enumerate(devices):
                device_dict = dict(device)
                device_list.append(device_dict)
                print(f"  Device {i}: {device_dict}")
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': f'Found {len(devices)} devices',
                'devices': device_list,
                'step': 'discovery'
            }
            
        except Exception as e:
            print(f"✗ uhd.find() failed: {e}")
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Device discovery failed: {e}',
                'step': 'discovery',
                'traceback': traceback.format_exc()
            }
    
    def handle_connect_device(self, params):
        """Handle device connection"""
        if not self.uhd_imported:
            return {
                'type': ResponseType.ERROR.value,
                'message': 'UHD not imported'
            }
        
        try:
            device_args = params.get('device_args', '')
            print(f"🔌 Connecting to device: {device_args}")
            
            # Create USRP object
            self.usrp = self.uhd.usrp.MultiUSRP(device_args)
            self.device_info = {
                'pp_string': self.usrp.get_pp_string(),
                'mboard_name': self.usrp.get_mboard_name(),
                'num_mboards': self.usrp.get_num_mboards()
            }
            
            print("✓ Device connected successfully")
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Device connected successfully',
                'device_info': self.device_info
            }
            
        except Exception as e:
            print(f"✗ Device connection failed: {e}")
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Device connection failed: {e}',
                'traceback': traceback.format_exc()
            }
    
    def handle_disconnect_device(self):
        """Handle device disconnection"""
        try:
            if self.usrp:
                self.usrp = None
                self.tx_streamer = None
                self.rx_streamer = None
                self.device_info = None
                print("✓ Device disconnected")
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Device disconnected'
            }
            
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Disconnect error: {e}'
            }
    
    def handle_get_status(self):
        """Get current server status"""
        return {
            'type': ResponseType.SUCCESS.value,
            'message': 'Status retrieved',
            'status': {
                'uhd_imported': self.uhd_imported,
                'device_connected': self.usrp is not None,
                'device_info': self.device_info
            }
        }
    
    def handle_configure_device(self, params):
        """Configure device parameters"""
        if not self.usrp:
            return {
                'type': ResponseType.ERROR.value,
                'message': 'No device connected'
            }
        
        try:
            # Basic configuration
            if 'sample_rate' in params:
                self.usrp.set_rx_rate(params['sample_rate'])
                self.usrp.set_tx_rate(params['sample_rate'])
            
            if 'center_freq' in params:
                self.usrp.set_rx_freq(params['center_freq'])
                self.usrp.set_tx_freq(params['center_freq'])
            
            if 'rx_gain' in params:
                self.usrp.set_rx_gain(params['rx_gain'])
            
            if 'tx_gain' in params:
                self.usrp.set_tx_gain(params['tx_gain'])
            
            print("✓ Device configured")
            
            return {
                'type': ResponseType.SUCCESS.value,
                'message': 'Device configured successfully'
            }
            
        except Exception as e:
            return {
                'type': ResponseType.ERROR.value,
                'message': f'Configuration failed: {e}',
                'traceback': traceback.format_exc()
            }
    
    def handle_shutdown(self):
        """Handle server shutdown"""
        print("🛑 Shutdown requested")
        
        # Disconnect device first
        self.handle_disconnect_device()
        
        # Schedule server stop
        def stop_server():
            time.sleep(0.5)
            self.stop()
        
        threading.Thread(target=stop_server, daemon=True).start()
        
        return {
            'type': ResponseType.SUCCESS.value,
            'message': 'Server shutting down'
        }

def main():
    print("=" * 50)
    print("UHD Server - Standalone UHD Operations")
    print("=" * 50)
    
    server = UHDServer()
    
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