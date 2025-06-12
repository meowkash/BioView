import queue

from bioview.device import Device
from bioview.device.common import DisplayWorker, SaveWorker
from bioview.types import ConnectionStatus
from bioview.utils import get_channel_map

from .connect import ConnectWorker as UsrpController
from .process import ProcessWorker as UsrpProcessor
from .receive import ReceiveWorker as UsrpReceiver
from .transmit import TransmitWorker as UsrpTransmitter


class MultiUsrpDevice(Device):
    def __init__(self, config, save=False, display=False):
        super().__init__(device_type="multi_usrp")
        self.config = config

        self.handler = {}
        self.state = {}

        self.save = save
        self.display = display

        for cfg in config:
            dev_handler = UsrpDevice(config=cfg)
            dev_name = dev_handler.name
            dev_handler.logEvent.connect(self._log_message)
            dev_handler.connectionStateChanged.connect(
                lambda value: self._on_state_update(device=dev_name, new_state=value)
            )

            self.handler[dev_name] = dev_handler
            self.state[dev_name] = ConnectionStatus.DISCONNECTED

        self.threads = {}

        self.channel_mapping = None
        self.data_mapping = {}
        self._generate_channel_mapping()

    def _generate_channel_mapping(self):
        # [1] -  Generate channel internal:external mapping
        counter = 0
        for idx, cfg in enumerate(self.config):
            self.config[idx].absolute_channel_nums = [
                counter + val for val in cfg.rx_channels
            ]
            counter += len(cfg.rx_channels)

        # [2] - Generate usrp channel pair labels
        num_usrp_devices = len(self.config)
        rx_per_usrp = [len(x.rx_channels) for x in self.config]
        tx_per_usrp = [len(x.tx_channels) for x in self.config]
        self.channel_mapping = get_channel_map(
            n_devices=num_usrp_devices,
            rx_per_dev=rx_per_usrp,
            tx_per_dev=tx_per_usrp,
            balance=getattr(self, "balance", False),
            multi_pairs=getattr(self, "multi_pairs", None),
        )

        # [3] - Generate usrp channel pair labels:data queue index mapping
        counter = 0
        ch_map = self.channel_mapping
        for ridx in range(len(ch_map)):
            for tidx in range(len(ch_map[ridx])):
                label = ch_map[ridx][tidx]
                if label != "":
                    self.data_mapping[label] = ("usrp", counter)
                    counter += 1

        # [4] Add usrp Parameters
        # Populate list of all channel frequencies
        channel_ifs = [None] * len(self.channel_mapping)
        for cfg in self.config:
            for idx, abs_idx in enumerate(cfg.absolute_channel_nums):
                channel_ifs[abs_idx] = cfg.if_freq[idx]
        self.channel_ifs = channel_ifs

    def _on_state_update(self, device, new_state):
        self.state[device] = new_state

        inited = True
        for _, dev_state in self.state.items():
            if dev_state != ConnectionStatus.CONNECTED:
                inited = False
                break

        if inited:
            self.connectionStateChanged.emit(ConnectionStatus.CONNECTED)

    def connect(self):
        for handler in self.handler.values():
            handler.connect()

        super().connect()

    def run(self):
        # Start transceiving
        for handler in self.handler.values():
            handler.run()

        # Start processing
        self.threads["Process"] = UsrpProcessor(
            exp_config=self.exp_config,
            usrp_config=self.config,
            rx_queues=[x.rx_queue for x in self.handler],
            disp_queue=self.disp_queue,
            running=True,
            saving=self.saving_status,
        )

        # Connect saving
        # self.threads['Save'] = SaveWorker()

        # # Connect display
        # self.threads['Display'] = DisplayWorker()

    def stop(self):
        for handler in self.handler.values():
            handler.stop()

        for thread in self.threads.values():
            thread.stop()


class UsrpDevice(Device):
    def __init__(self, config):
        super().__init__(device_type="usrp")
        self.config = config
        self.name = config.get_param("device_name")
        self.rx_queue = queue.Queue()

    def connect(self):
        self.connect_thread = UsrpController(self.config)
        self.connect_thread.initSucceeded.connect(
            lambda usrp, tx_streamer, rx_streamer: self._on_connect_success(
                usrp=usrp, tx_streamer=tx_streamer, rx_streamer=rx_streamer
            )
        )

        super().connect()

    def run(self):
        if self.handler is None:
            self.logEvent.emit("error", "No USRP object found")
            return

        if self.tx_streamer is None:
            self.logEvent.emit("error", "No USRP Tx streamer found")
            return

        if self.rx_streamer is None:
            self.logEvent.emit("error", "No USRP Rx streamer found")
            return

        # Create transmitter thread
        self.threads["Transmit"] = UsrpTransmitter(
            config=self.config, usrp=self.handler, tx_streamer=self.tx_streamer
        )

        # Create receiver thread
        self.threads["Receive"] = UsrpReceiver(
            usrp=self.handler,
            config=self.config,
            rx_streamer=self.rx_streamer,
            rx_queue=self.rx_queue,
            running=True,
        )

        # Start threads
        super().run()

    def stop(self):
        return super().stop()

    def balance_gains(self):
        pass

    def sweep_frequency(self):
        pass

    def _on_connect_success(self, usrp, tx_streamer, rx_streamer, idx=0):
        self.handler = usrp
        self.tx_streamer = tx_streamer
        self.rx_streamer = rx_streamer

        # Update status bar
        self.connectionStateChanged.emit(ConnectionStatus.CONNECTED)


def get_device_object(config):
    if isinstance(config, tuple) or isinstance(config, list):
        return MultiUsrpDevice(config=config)
    else:
        cfg_list = [config]
        return MultiUsrpDevice(config=cfg_list)


__all__ = ["MultiUsrpDevice", "get_device_object"]
