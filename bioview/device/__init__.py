from bioview.types import (
    BiopacConfiguration,
    Device,
    ExperimentConfiguration,
    MultiUsrpConfiguration,
)


def _check_type(obj, typ):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return all(isinstance(x, typ) for x in obj)

    return isinstance(obj, typ)


def get_device_object(device_name, config, save, exp_config: ExperimentConfiguration):
    if _check_type(config, MultiUsrpConfiguration):
        from .usrp import get_device_object

        return get_device_object(
            device_name=device_name,
            config=config,
            save=save,
            save_path=exp_config.get_save_path(device_name),
        )
    elif _check_type(config, BiopacConfiguration):
        from .biopac import get_device_object

        return get_device_object(
            device_name=device_name,
            config=config,
            save=save,
            save_path=exp_config.get_save_path(device_name),
        )
    else:
        return None


__all__ = ["get_device_object"]
