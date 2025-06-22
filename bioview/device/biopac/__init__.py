from .device import BiopacDevice
from .config import BiopacConfiguration

def get_device_object(device_name, config, save=False, save_path=None):
    return BiopacDevice(
        device_name=device_name, config=config, save=save, save_path=save_path
    )


__all__ = ["BiopacDevice", "BiopacConfiguration", "get_device_object"]
