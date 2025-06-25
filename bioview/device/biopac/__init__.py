from .device import BiopacDevice
from .config import BiopacConfiguration

def get_device_object(device_name, config, resp_queue, data_queue, save=False, save_path=None):
    return BiopacDevice(
        device_name=device_name, config=config, resp_queue=resp_queue, data_queue=data_queue, save=save, save_path=save_path
    )


__all__ = ["BiopacDevice", "BiopacConfiguration", "get_device_object"]
