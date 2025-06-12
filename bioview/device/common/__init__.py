# Core functionality that should always be available
from .display import DisplayWorker
from .save import SaveWorker

__all__ = ["DisplayWorker", "SaveWorker"]

# Optional functionality with third-party dependencies
try:
    from .instructions import InstructionWorker

    __all__.append("InstructionWorker")
except ImportError:
    pass
