import subprocess
import uhd

def rename_uhd_device_eeprom(device_args, new_name, exe_path = None):
    """
    Rename UHD device by writing to EEPROM using usrp_burn_mb_eeprom
    
    Args:
        device_args: Device identification (e.g., "type=b200" or "serial=12345678")
        new_name: New name for the device
    """
    if exe_path is None: 
        cmd = [
            "usrp_burn_mb_eeprom",
            f"--args={device_args}",
            f"--values=name={new_name}"
        ]
    else: 
        cmd = [
            exe_path,
            f"--args={device_args}",
            f"--values=name={new_name}"
        ]
    
    try:
        print(f"Writing name '{new_name}' to device EEPROM...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Success! Device renamed to: {new_name}")
        print("Note: You may need to power cycle the device for changes to take effect.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error renaming device: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("usrp_burn_mb_eeprom not found. Make sure UHD is installed and in PATH.")
        return False

def verify_device_name(device_args):
    """Verify the device name by reading EEPROM"""
    cmd = [
        "usrp_burn_mb_eeprom",
        f"--args={device_args}",
        "--read-all"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Current EEPROM contents:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error reading EEPROM: {e}")
        return False

# Usage example
if __name__ == "__main__":
    # For B210 device (you can also use serial number instead)
    addr = uhd.find('')[0]
    device_args = f"serial={addr['serial']}"  # or "serial=YOUR_SERIAL"
    new_name = "MyB210_19"
    
    exe_path = 'C:/Program Files/UHD/lib/uhd/utils/usrp_burn_mb_eeprom.exe'
    
    # Rename the device
    rename_uhd_device_eeprom(device_args, new_name, exe_path=exe_path)
    
    # Verify the change
    print(f"\nTesting device discovery by name:")
        
    # Test that the device can now be found by name
    addr = uhd.find('')[0]
    print(addr['name'])