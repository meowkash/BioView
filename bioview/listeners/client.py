#!/usr/bin/env python3
"""
UHD Client - Test client to debug UHD server operations
Use this to test UHD functionality step by step
"""

import socket
import json
import time
import threading
from enum import Enum

class CommandType(Enum):
    PING = "ping"
    DISCOVER_DEVICES = "discover_devices"
    CONNECT_DEVICE = "connect_device"
    DISCONNECT_DEVICE = "disconnect_device"
    GET_STATUS = "get_status"
    CONFIGURE_DEVICE = "configure_device"
    SHUTDOWN = "shutdown"

class UHDClient:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Connect to UHD server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✓ Connected to UHD server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("✓ Disconnected from server")
    
    def send_command(self, command_type, params=None):
        """Send command to server and get response"""
        if not self.connected:
            return {"error": "Not connected to server"}
        
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
            return {"error": f"Communication error: {e}"}
    
    def ping(self):
        """Test server connectivity"""
        print("\n📡 Testing server connectivity...")
        response = self.send_command(CommandType.PING)
        
        if response.get('type') == 'success':
            print("✓ Server is responding")
            server_info = response.get('server_info', {})
            print(f"  Python: {server_info.get('python_version', 'unknown')}")
            print(f"  Platform: {server_info.get('platform', 'unknown')}")
            print(f"  UHD Imported: {server_info.get('uhd_imported', False)}")
        else:
            print(f"✗ Server ping failed: {response}")
        
        return response
    
    def discover_devices(self):
        """Discover USRP devices"""
        print("\n🔍 Discovering USRP devices...")
        print("⚠️  This is the step that typically crashes!")
        
        response = self.send_command(CommandType.DISCOVER_DEVICES)
        
        if response.get('type') == 'success':
            step = response.get('step', 'unknown')
            if step == 'import':
                print("✓ UHD import successful")
                print("  Now run discover again to test uhd.find()")
            elif step == 'discovery':
                devices = response.get('devices', [])
                print(f"✓ Device discovery successful! Found {len(devices)} devices")
                for i, device in enumerate(devices):
                    print(f"  Device {i}: {device}")
        else:
            step = response.get('step', 'unknown')
            error_msg = response.get('message', 'Unknown error')
            print(f"✗ Device discovery failed at step '{step}': {error_msg}")
            
            if 'traceback' in response:
                print("Traceback:")
                print(response['traceback'])
        
        return response
    
    def connect_device(self, device_args=""):
        """Connect to a specific device"""
        print(f"\n🔌 Connecting to device: '{device_args}'")
        
        response = self.send_command(CommandType.CONNECT_DEVICE, {
            'device_args': device_args
        })
        
        if response.get('type') == 'success':
            print("✓ Device connection successful")
            device_info = response.get('device_info', {})
            if 'mboard_name' in device_info:
                print(f"  Device: {device_info['mboard_name']}")
        else:
            print(f"✗ Device connection failed: {response.get('message')}")
        
        return response
    
    def configure_device(self, config):
        """Configure device parameters"""
        print(f"\n⚙️  Configuring device...")
        
        response = self.send_command(CommandType.CONFIGURE_DEVICE, config)
        
        if response.get('type') == 'success':
            print("✓ Device configuration successful")
        else:
            print(f"✗ Device configuration failed: {response.get('message')}")
        
        return response
    
    def get_status(self):
        """Get server status"""
        print("\n📊 Getting server status...")
        
        response = self.send_command(CommandType.GET_STATUS)
        
        if response.get('type') == 'success':
            status = response.get('status', {})
            print(f"✓ Status retrieved")
            print(f"  UHD Imported: {status.get('uhd_imported', False)}")
            print(f"  Device Connected: {status.get('device_connected', False)}")
        else:
            print(f"✗ Status request failed: {response.get('message')}")
        
        return response
    
    def shutdown_server(self):
        """Shutdown the server"""
        print("\n🛑 Shutting down server...")
        
        response = self.send_command(CommandType.SHUTDOWN)
        
        if response.get('type') == 'success':
            print("✓ Server shutdown initiated")
        else:
            print(f"✗ Shutdown failed: {response.get('message')}")
        
        return response

def interactive_test():
    """Interactive testing mode"""
    client = UHDClient()
    
    print("=" * 60)
    print("UHD Client - Interactive Testing")
    print("=" * 60)
    
    # Connect to server
    if not client.connect():
        print("❌ Could not connect to server. Make sure uhd_server.py is running!")
        return
    
    try:
        while True:
            print("\n" + "=" * 40)
            print("Available commands:")
            print("1. ping           - Test server connectivity")
            print("2. discover       - Discover devices (THE CRASH TEST)")
            print("3. status         - Get server status")
            print("4. connect        - Connect to device")
            print("5. configure      - Configure device")
            print("6. shutdown       - Shutdown server")
            print("7. quit           - Exit client")
            
            choice = input("\nEnter command (1-7): ").strip()
            
            if choice == '1':
                client.ping()
            elif choice == '2':
                client.discover_devices()
            elif choice == '3':
                client.get_status()
            elif choice == '4':
                device_args = input("Enter device args (empty for auto): ").strip()
                client.connect_device(device_args)
            elif choice == '5':
                config = {
                    'sample_rate': 1e6,
                    'center_freq': 2.4e9,
                    'rx_gain': 30,
                    'tx_gain': 10
                }
                client.configure_device(config)
            elif choice == '6':
                client.shutdown_server()
                break
            elif choice == '7':
                break
            else:
                print("Invalid choice")
                
    except KeyboardInterrupt:
        print("\nKeyboard interrupt")
    finally:
        client.disconnect()

def automated_test():
    """Automated test sequence"""
    client = UHDClient()
    
    print("=" * 60)
    print("UHD Client - Automated Test Sequence")
    print("=" * 60)
    
    if not client.connect():
        print("❌ Could not connect to server")
        return
    
    try:
        # Test sequence
        tests = [
            ("Server Ping", lambda: client.ping()),
            ("Device Discovery", lambda: client.discover_devices()),
            ("Server Status", lambda: client.get_status()),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running test: {test_name}")
            try:
                result = test_func()
                success = result.get('type') == 'success'
                results.append((test_name, success, result.get('message', '')))
                
                if success:
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
                    
                time.sleep(1)  # Pause between tests
                
            except Exception as e:
                print(f"❌ {test_name} CRASHED: {e}")
                results.append((test_name, False, str(e)))
        
        # Summary
        print("\n" + "=" * 40)
        print("TEST RESULTS SUMMARY:")
        print("=" * 40)
        
        for test_name, success, message in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}: {message}")
            
    finally:
        client.disconnect()

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'auto':
        automated_test()
    else:
        interactive_test()

if __name__ == "__main__":
    main()