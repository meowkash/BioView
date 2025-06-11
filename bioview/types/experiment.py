from .config import Configuration
from bioview.utils import get_unique_path
from bioview.constants import BASE_USRP_CONFIG


# A collection of (mostly) device-agnostic configuration parameters
class ExperimentConfiguration(Configuration):
    def __init__(
        self,
        save_dir: str,
        file_name: str,
        save_ds: int,
        disp_ds: int,
        disp_filter_spec: dict,
        disp_channels: list = None,
        save_phase: bool = True,
        show_phase: bool = False,
        loop_instructions: bool = True,
        instruction_type: str = None,
        instruction_file: list[str] = [],
        instruction_interval: int = 5000,
        **kwargs,
    ):
        super().__init__()

        self.save_dir = save_dir
        self.file_name = file_name
        self.save_ds = save_ds
        self.disp_ds = disp_ds
        self.disp_filter_spec = disp_filter_spec
        self.disp_channels = disp_channels

        # USRP-Specific Configuration Variables
        self.if_filter_bw = kwargs.get("if_filter_bw", BASE_USRP_CONFIG["if_filter_bw"])
        self.save_phase = save_phase
        self.show_phase = show_phase

        # Declare mappings
        self.channel_mapping = None
        self.channel_ifs = {}
        self.data_mapping = {}
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

    def get_disp_freq(self):
        return self.get_param("samp_rate", 1e6) / (self.save_ds * self.disp_ds)

    def get_display_channels(self, device):
        channels = []
        for idx, ch_key in enumerate(self.disp_channels):
            ch_meta = self.data_mapping[ch_key]
            if ch_meta[0] == device:
                channels.append(ch_meta[1])

        return channels
