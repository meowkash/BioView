from bioview.types import BiopacConfiguration, UsrpConfiguration

from .device import Device


def _check_type(obj, typ):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return all(isinstance(x, typ) for x in obj)

    return isinstance(obj, typ)


def get_device_object(config):
    if _check_type(config, UsrpConfiguration):
        from .usrp import get_device_object

        return get_device_object(config)
    elif _check_type(config, BiopacConfiguration):
        from .biopac import get_device_object

        return get_device_object(config)
    else:
        return None


__all__ = ["Device", "get_device_handler"]
