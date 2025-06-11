import ctypes
import os
from pathlib import Path

from bioview.constants import BIOPAC_CONNECTION_CODES
from .caches import get_mpdev_path, update_mpdev_path


def load_mpdev_dll(custom_loc: str = None):
    dll = None
    try:
        dll = ctypes.CDLL("mpdev.dll")
        return
    except FileNotFoundError:
        print("mpdev.dll is not located in $PATH")

    # Check custom loc
    if custom_loc is not None:
        dll_locs = Path(custom_loc).glob("**/mpdev.dll")
        for loc in dll_locs:
            dll = ctypes.CDLL(loc)
            return dll

    # Check root diretory - Check cache before searching
    dll_path = get_mpdev_path()
    if dll_path is not None:
        return ctypes.CDLL(dll_path)
    else:
        sys_dir = Path(os.path.abspath(os.sep))
        dll_locs = sys_dir.glob("Program Files*/BIOPAC*/**/x64/mpdev.dll")

        for loc in dll_locs:
            update_mpdev_path(loc)
            dll = ctypes.CDLL(loc)
            return dll

    return None


def wrap_result_code(result, stage=""):
    result_code = BIOPAC_CONNECTION_CODES.get(result, "INVALID_CODE")
    if result_code == "MPSUCCESS":
        return True
    else:
        raise Exception(f"{stage} Failure - {result_code}")
