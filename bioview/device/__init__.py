from bioview.datatypes import ExperimentConfiguration

from .usrp import MultiUsrpConfiguration, UsrpConfiguration
from .biopac import BiopacConfiguration

def _check_type(obj, typ):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return all(isinstance(x, typ) for x in obj)

    return isinstance(obj, typ)

def get_device_object(device_name, config, resp_queue, data_queue, save, exp_config: ExperimentConfiguration):
    if _check_type(config, MultiUsrpConfiguration):
        from .usrp import get_device_object
        func = get_device_object
    elif _check_type(config, BiopacConfiguration):
        from .biopac import get_device_object
        func = get_device_object
    else:
        return None
    
    return func(
            device_name=device_name,
            config=config,
            resp_queue=resp_queue, 
            data_queue=data_queue, 
            save=save,
            save_path=exp_config.get_save_path(device_name),
        )

__all__ = ["MultiUsrpConfiguration", "UsrpConfiguration", "BiopacConfiguration", "get_device_object"]
