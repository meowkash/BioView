from bioview.constants import BASE_USRP_CONFIG
from bioview.utils import get_unique_path

from .config import Configuration


# A collection of (mostly) device-agnostic configuration parameters
class ExperimentConfiguration(Configuration):
    def __init__(
        self,
        save_dir: str,
        file_name: str,
        display_sources: dict = {},
        loop_instructions: bool = True,
        instruction_type: str = None,
        instruction_file: list[str] = [],
        instruction_interval: int = 5000,
        **kwargs,
    ):
        super().__init__()

        self.save_dir = save_dir
        self.file_name = file_name

        # Common functionality
        self.display_sources = display_sources

        # Declare mappings
        self.channel_ifs = {}
        self.display_sources = []  # Collection of all things to display

        ### Common functionality for instructions
        self.loop_instructions = loop_instructions
        self.instruction_type = instruction_type  # Typically audio or text
        self.instruction_file = instruction_file
        self.instruction_interval = instruction_interval

    def get_log_path(self):
        return get_unique_path(self.save_dir, f"{self.file_name}.log")

    def get_save_path(self, sensor="usrp"):
        return get_unique_path(self.save_dir, f"{self.file_name}_{sensor}.h5")
