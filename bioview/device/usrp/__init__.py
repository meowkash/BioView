from .config import MultiUsrpConfiguration, UsrpConfiguration
from .device import MultiUsrpDevice

def get_device_object(device_name, config, resp_queue, data_queue, save=False, save_path=None):
    return MultiUsrpDevice(
        device_name=device_name, config=config, resp_queue=resp_queue, data_queue=data_queue, save=save, save_path=save_path
    )


__all__ = ["MultiUsrpDevice", "MultiUsrpConfiguration", "UsrpConfiguration", "get_device_object"]
