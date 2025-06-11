from .config import Configuration
from bioview.constants import BASE_USRP_CONFIG


class UsrpConfiguration(Configuration):
    def __init__(
        self,
        device_name: str,
        if_freq: list,
        if_bandwidth: int,
        rx_gain: list,
        tx_gain: list,
        samp_rate: int,
        carrier_freq: int,
        **kwargs,
    ):
        super().__init__()

        # Add inputs
        self.device_name = device_name
        self.if_freq = if_freq
        self.if_bandwidth = if_bandwidth
        self.rx_gain = rx_gain
        self.tx_gain = tx_gain
        self.samp_rate = samp_rate
        self.carrier_freq = carrier_freq

        # Add base config
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
