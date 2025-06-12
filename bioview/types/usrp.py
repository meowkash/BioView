from bioview.constants import BASE_USRP_CONFIG

from .config import Configuration


class UsrpConfiguration(Configuration):
    def __init__(
        self,
        device_name: str,
        if_freq: list,
        rx_gain: list,
        tx_gain: list,
        carrier_freq: int,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Add inputs
        self.device_name = device_name
        self.if_freq = if_freq
        self.rx_gain = rx_gain
        self.tx_gain = tx_gain
        self.carrier_freq = carrier_freq

        self.save_ds = kwargs.get("save_ds", BASE_USRP_CONFIG["save_ds"])
        self.display_ds = kwargs.get("disp_ds", BASE_USRP_CONFIG["disp_ds"])
        self.if_filter_bw = kwargs.get("if_filter_bw", BASE_USRP_CONFIG["if_filter_bw"])
        self.samp_rate = kwargs.get("samp_rate", BASE_USRP_CONFIG["samp_rate"])

        # Add basic configuration
        self.tx_amplitude = kwargs.get("tx_amplitude", BASE_USRP_CONFIG["tx_amplitude"])
        self.rx_channels = kwargs.get("rx_channels", BASE_USRP_CONFIG["rx_channels"])
        self.tx_channels = kwargs.get("tx_channels", BASE_USRP_CONFIG["tx_channels"])
        self.rx_subdev = kwargs.get("rx_subdev", BASE_USRP_CONFIG["rx_subdev"])
        self.tx_subdev = kwargs.get("tx_subdev", BASE_USRP_CONFIG["tx_subdev"])
        self.cpu_format = kwargs.get("cpu_format", BASE_USRP_CONFIG["cpu_format"])
        self.wire_format = kwargs.get("wire_format", BASE_USRP_CONFIG["wire_format"])
        self.clock = kwargs.get("clock", BASE_USRP_CONFIG["clock"])
        self.pps = kwargs.get("pps", BASE_USRP_CONFIG["pps"])

        # Set-up default absolute channel mapping, assuming single device.
        # This assumes that Tx/Rx are always used in pairs
        # This must be updated if using MIMO with multiple USRPs
        self.absolute_channel_nums = self.tx_channels

    def get_filter_bw(self):
        if not (
            isinstance(self.if_filter_bw, list) or isinstance(self.if_filter_bw, tuple)
        ):
            return [self.if_filter_bw for _ in self.tx_channels]
        elif len(self.if_filter_bw) == len(self.tx_channels):
            return self.if_filter_bw
