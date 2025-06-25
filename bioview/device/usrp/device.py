import queue

from bioview.types import Device
from bioview.device.common import DisplayWorker, SaveWorker
from bioview.types import (
    ConnectionStatus,
    DataSource
)
from bioview.utils import get_channel_map, emit_signal

from .config import MultiUsrpConfiguration, UsrpConfiguration
from .connect import ConnectWorker
from .process import ProcessWorker
from .receive import ReceiveWorker
from .transmit import TransmitWorker

class MultiUsrpDevice(Device):
    def __init__(
        self,
        device_name,
        config: MultiUsrpConfiguration,
        resp_queue, 
        data_queue, 
        save=False,
        save_path=None,
        display=True,
    ):
        super().__init__(
            device_name=device_name,
            config=config,
            resp_queue=resp_queue,
            data_queue=data_queue,
            device_type="multi_usrp",
            save=save,
            save_path=save_path,
            display=display,
        )

        self.handler = {}
        self.state = {}

        self.if_filter_bw = []

        for dev_name, dev_cfg in config.devices.items():
            dev_handler = UsrpDevice(device_name=dev_name, config=dev_cfg)
            self.if_filter_bw.extend(dev_cfg.get_filter_bw())
            dev_handler.log_event = self.log_event
            dev_handler.connection_state_changed = self.connection_state_changed(
                lambda value, dev_name=dev_name: self._on_state_update(
                    device=dev_name, new_state=value
                )
            )

            self.handler[dev_name] = dev_handler
            self.state[dev_name] = ConnectionStatus.DISCONNECTED

    def _populate_data_sources(self):
        """
        We can arrange multiple USRPs in a variety of configurations, including -
        1. MIMO
        2. Multi-Frequency Band
        3. DPIC
        The above are supported configurations and the list may keep growing.
        In each case, our data source needs to know about what Tx and Rx
        (absolute indices) it is using. Hence, the code below does the following -
        1. From relative Tx/Rx mapping (which is what the API spec gives us), we
        create absolute Tx/Rx mapping
        2. We generate channel mapping and ensure each data source knows its sources
        """
        num_usrp_devices = len(self.config.devices)

        # Generate absolute Tx/Rx mapping across all USRP devices
        counter = 0
        for dev_cfg in self.config.devices.values():
            dev_cfg.absolute_channel_nums = [
                counter + val for val in dev_cfg.rx_channels
            ]
            counter += len(dev_cfg.rx_channels)

        # Generate sources with mapping
        rx_per_usrp = [len(x.rx_channels) for x in self.config.devices.values()]
        tx_per_usrp = [len(x.tx_channels) for x in self.config.devices.values()]
        self.data_sources = get_channel_map(
            device=self,
            n_devices=num_usrp_devices,
            rx_per_dev=rx_per_usrp,
            tx_per_dev=tx_per_usrp,
            balance=getattr(self, "balance", False),
            multi_pairs=getattr(self, "multi_pairs", None),
        )

        # Populate list of all channel frequencies - Number of Tx/Rx
        channel_ifs = [None] * sum(rx_per_usrp)
        for cfg in self.config.devices.values():
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
            emit_signal(self.connection_state_changed, ConnectionStatus.CONNECTED)

    def connect(self):
        for handler in self.handler.values():
            handler.connect()

    def run(self):
        # Start transceiving
        for handler in self.handler.values():
            handler.run()

        # Start processing
        self.threads["Process"] = ProcessWorker(
            config=self.config,
            channel_ifs=self.channel_ifs,
            if_filter_bw=self.if_filter_bw,
            data_sources=self.data_sources,
            rx_queues=[x.rx_queue for x in self.handler.values()],
            save_queue=self.save_queue,
            disp_queue=self.display_queue,
            running=True,
        )

        # Start saving
        if self.config.get_param("save_phase", True):
            self.num_channels = 2 * len(self.data_sources)
        else:
            self.num_channels = len(self.data_sources)

        if self.save and self.save_path is not None:
            self.threads["Save"] = SaveWorker(
                save_path=self.save_path,
                data_queue=self.save_queue,
                num_channels=self.num_channels,
                running=True,
            )

        # Create display thread
        if self.display:
            self.threads["Display"] = DisplayWorker(
                config=self.config,
                data_queue=self.display_queue,
                running=True,
            )
            self.threads["Display"].data_ready = self.data_ready

        # Start threads
        super().run()

    def stop(self):
        for handler in self.handler.values():
            handler.stop()

        for thread in self.threads.values():
            thread.stop()


class UsrpDevice(Device):
    def __init__(self, device_name, config: UsrpConfiguration):
        super().__init__(device_name=device_name, config=config, device_type="usrp")

        self.rx_queue = queue.Queue()

    def _populate_data_sources(self):
        pass  # No fancy data source mapping is needed here

    def connect(self):
        self.connect_thread = ConnectWorker(self.config)
        self.connect_thread.init_succeeded = lambda usrp, tx_streamer, rx_streamer: self._on_connect_success(
                usrp=usrp, tx_streamer=tx_streamer, rx_streamer=rx_streamer
            )

        self.connect_thread.init_failed = self._on_connect_failure
        self.connect_thread.log_event = self.log_event
        
        # Let frontend know we are connecting
        emit_signal(self.connection_state_changed, ConnectionStatus.CONNECTING)

        self.connect_thread.start()
        self.connect_thread.wait()

    def run(self):
        if self.handler is None:
            emit_signal(self.log_event, "error", "No USRP object found")
            return

        if self.tx_streamer is None:
            emit_signal(self.log_event, "error", "No USRP Tx streamer found")
            return

        if self.rx_streamer is None:
            emit_signal(self.log_event, "error", "No USRP Rx streamer found")
            return

        # Create transmitter thread
        self.threads["Transmit"] = TransmitWorker(
            config=self.config, usrp=self.handler, tx_streamer=self.tx_streamer
        )

        # Create receiver thread
        self.threads["Receive"] = ReceiveWorker(
            usrp=self.handler,
            config=self.config,
            rx_streamer=self.rx_streamer,
            rx_queue=self.rx_queue,
            running=True,
        )

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
        emit_signal(self.connection_state_changed, ConnectionStatus.CONNECTED)
