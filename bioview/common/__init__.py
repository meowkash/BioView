# Core functionality that should always be available
from .displayer import DisplayWorker as Displayer
from .saver import SaveWorker as Saver

__all__ = ["Displayer", "Saver"]

# Optional functionality with third-party dependencies
try:
    from .instructions import InstructionsWorker as Instructor

    __all__.append("Instructor")
except ImportError:
    pass
