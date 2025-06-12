from bioview.constants import BASE_USRP_CONFIG
from bioview.utils import get_unique_path

from .config import Configuration


# A collection of (mostly) device-agnostic configuration parameters
class ExperimentConfiguration(Configuration):
    def __init__(
        self,
        save_dir: str,
        file_name: str,
        save_ds: dict,
        disp_ds: dict,
        samp_rate: dict,
        disp_channels: dict = {},
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

        # Common functionality
        self.save_ds = save_ds
        self.disp_ds = disp_ds
        self.samp_rate = samp_rate
        self.disp_channels = disp_channels

        # USRP-Specific Configuration Variables
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

    def get_disp_freq(self, sensor):
        if sensor in self.samp_rate.keys():
            samp_rate = self.samp_rate[sensor]
        else:
            return

        if sensor in self.save_ds.keys():
            save_ds = self.save_ds[sensor]
        else:
            return

        if sensor in self.disp_ds.keys():
            disp_ds = self.save_ds[sensor]
        else:
            return

        return samp_rate / (save_ds * disp_ds)

    def get_display_channels(self, device):
        channels = []
        for _, ch_key in enumerate(self.disp_channels):
            ch_meta = self.data_mapping[ch_key]
            if ch_meta[0] == device:
                channels.append(ch_meta[1])

        return channels
