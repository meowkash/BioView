# A multi-processing version of the old controller.
import logging
import multiprocessing
from pathlib import Path
from threading import Thread

from PyQt6.QtCore import QMutex
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QStatusBar, QVBoxLayout, QWidget

from bioview.device.common import InstructionWorker
from bioview.device import MultiUsrpConfiguration
from bioview.types import (
    CommandType,
    ConnectionStatus,
    DataSource,
    ExperimentConfiguration,
    Message,
    RunningStatus,
)
from bioview.ui import (
    AnnotateEventPanel,
    AppControlPanel,
    DeviceStatusPanel,
    ExperimentSettingsPanel,
    LogDisplayPanel,
    PlotGrid,
    TextDialog,
    UsrpDeviceConfigPanel,
)
from bioview.listeners import BackendListener, FrontendListener

class ViewerMP(QMainWindow):
    def __init__(
        self,
        device_config: dict,
        exp_config: ExperimentConfiguration,
    ):
        super().__init__()
        self.mutex = QMutex()

        self.exp_config = exp_config
        self.device_config = device_config

        self.exp_config.available_channels = []

        # Track state
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.running_status = RunningStatus.NOINIT
        self.saving_status = False

        # Create runners
        self.runners = {}
        # Everyone shares data queue as it goes into graphical display
        self.data_queue = multiprocessing.Queue()
        # Responses from all backends are shared since they are used for logging, etc
        self.resp_queue = multiprocessing.Queue()

        for dev_name, dev_cfg in device_config.items():
            cmd_queue = multiprocessing.Queue()
            
            process = BackendListener(
                id=dev_name,
                config=dev_cfg,
                exp_config=exp_config,
                cmd_queue=cmd_queue,
                resp_queue=self.resp_queue, 
                data_queue=self.data_queue,
                save=self.saving_status,
            )
            self.runners[dev_name] = {
                "process": process,
                "config": dev_cfg,
                "state": ConnectionStatus.DISCONNECTED,  # Initialize device state
                "cmd_queue": cmd_queue,
            }
            process.start()

        # Track instruction
        if exp_config.get_param("instruction_type") is None:
            self.enable_instructions = False
        else:
            self.enable_instructions = True

        self.instruction_dialog = None
        if exp_config.get_param("instruction_type") == "text":
            self.instruction_dialog = TextDialog()

        # Set up UI
        self._init_ui()

        # Common Threads
        self.instructions_thread = None

        # Enable Logging
        self._connect_logging()

        # Enable listening for IPC
        self.listener = FrontendListener(self.data_queue, self.resp_queue)
        self._start_listener()

    def _init_ui(self):
        # Define main wndow
        self.setWindowTitle("BioView")
        iconDir = (
            Path(__file__).resolve().parent.parent / "docs" / "assets" / "icon.png"
        )

        self.setWindowIcon(QIcon(str(iconDir)))
        screen = QGuiApplication.primaryScreen().geometry()
        width = screen.width()
        height = screen.height()
        self.setGeometry(
            int(0.2 * width), int(0.1 * height), int(0.6 * width), int(0.8 * height)
        )

        # Create central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top shelf container
        top_layout = QHBoxLayout()

        # All controls are in one container
        controls_layout = QVBoxLayout()

        # Connect/Start/Stop/Balance Signal Buttons
        self.app_control_panel = AppControlPanel()
        controls_layout.addWidget(self.app_control_panel, stretch=1)

        # Connect signal handlers
        self.app_control_panel.connectionInitiated.connect(self.connect)
        # self.app_control_panel.disconnectRequested.connect(self.disconnect)
        self.app_control_panel.startRequested.connect(self.start)
        self.app_control_panel.stopRequested.connect(self.stop)
        self.app_control_panel.saveRequested.connect(self.update_save_state)
        self.app_control_panel.instructionsEnabled.connect(self.toggle_instructions)
        self.app_control_panel.balanceRequested.connect(self.perform_gain_balancing)
        self.app_control_panel.sweepRequested.connect(self.perform_frequency_sweep)

        experiment_layout = QHBoxLayout()

        # Experiment Control Panel
        self.experiment_settings_panel = ExperimentSettingsPanel(self.exp_config)
        experiment_layout.addWidget(self.experiment_settings_panel, stretch=1)
        # Connect handlers
        self.experiment_settings_panel.timeWindowChanged.connect(
            self.handle_time_window_change
        )
        self.experiment_settings_panel.gridLayoutChanged.connect(
            self.handle_grid_layout_change
        )
        self.experiment_settings_panel.addChannelRequested.connect(
            self.handle_add_source
        )
        self.experiment_settings_panel.removeChannelRequested.connect(
            self.handle_remove_source
        )

        # USRP Device Config Panel(s)
        usrp_cfg = []
        for runner in self.runners.values():
            if isinstance(runner["config"], MultiUsrpConfiguration):
                usrp_cfg = runner["config"].devices.values()

        self.usrp_config_panel = [None] * len(usrp_cfg)
        for idx, cfg in enumerate(usrp_cfg):
            self.usrp_config_panel[idx] = UsrpDeviceConfigPanel(cfg)
            experiment_layout.addWidget(self.usrp_config_panel[idx], stretch=1)

        controls_layout.addLayout(experiment_layout, stretch=4)
        top_layout.addLayout(controls_layout, stretch=3)

        # Metadata Panels
        self.meta_panels = QVBoxLayout()
        # Status Panel - Experiment Log goes here
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.log_display_panel = LogDisplayPanel(logger=self.logger)
        self.meta_panels.addWidget(self.log_display_panel, stretch=3)

        # Annotation Panel
        self.annotate_event_panel = AnnotateEventPanel(self.exp_config)
        self.meta_panels.addWidget(self.annotate_event_panel, stretch=2)
        top_layout.addLayout(self.meta_panels, stretch=2)

        main_layout.addLayout(top_layout)

        # Plot Grid
        self.plot_grid = PlotGrid(self.exp_config)
        main_layout.addWidget(self.plot_grid)

        central_widget.setLayout(main_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.device_status_panel = DeviceStatusPanel(self.runners)

        # Add device status panel to status bar (on the right side)
        self.status_bar.addPermanentWidget(self.device_status_panel)
        # Add some info text to status bar
        self.status_bar.showMessage("Ready")

    def _connect_logging(self):
        self.plot_grid.logEvent.connect(self.log_display_panel.log_message)
        for _, panel in enumerate(self.usrp_config_panel):
            panel.logEvent.connect(self.log_display_panel.log_message)

    def _start_listener(self):
        # Connect signals
        self.listener.dataReady.connect(self.plot_grid.add_new_data)
        self.listener.logEvent.connect(self.log_display_panel.log_message)
        self.listener.connectionStateChanged.connect(self.update_connection_status)

        # Start listening
        self.listener_thread = Thread(target=self.listener.start)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def connect(self):
        # Disable button during initialization
        self.running_status = RunningStatus.NOINIT
        self.connection_status = ConnectionStatus.CONNECTING
        self.update_buttons()

        connect_cmd = Message(
            msg_type=CommandType.CONNECT,
        )

        for runner in self.runners.values():
            runner["cmd_queue"].put(connect_cmd)

    def disconnect(self):
        # Disable button during initialization
        self.running_status = RunningStatus.NOINIT
        self.connection_status = ConnectionStatus.DISCONNECTED

        disconnect_cmd = Message(
            msg_type=CommandType.DISCONNECT,
        )

        for runner in self.runners.values():
            runner["cmd_queue"].put(disconnect_cmd)

        self.update_buttons()

    def start(self):
        # Update state
        self.running_status = RunningStatus.RUNNING
        self.connection_status = ConnectionStatus.CONNECTED

        start_cmd = Message(
            msg_type=CommandType.START,
        )

        for runner in self.runners.values():
            runner["cmd_queue"].put(start_cmd)

        # Create instruction thread
        if self.enable_instructions:
            self.instructions_thread = InstructionWorker(config=self.exp_config)
            if self.instruction_dialog is not None:
                self.instructions_thread.textUpdate.connect(
                    self.instruction_dialog.update_instruction_text
                )
            self.instructions_thread.logEvent.connect(
                self.log_display_panel.log_message
            )
            self.instructions_thread.start()

        # Update UI
        self.update_buttons()

    def stop(self):
        # Update state
        self.running_status = RunningStatus.STOPPED
        self.connection_status = ConnectionStatus.CONNECTED

        stop_cmd = Message(
            msg_type=CommandType.STOP,
        )

        for runner in self.runners.values():
            runner["cmd_queue"].put(stop_cmd)

        # Stop instruction
        if self.instructions_thread is not None:
            self.instructions_thread.stop()

        # Update UI
        self.update_buttons()

    def perform_gain_balancing(self):
        # for handler in self.device_handlers.values():
        #     if handler.device_type == "usrp" or handler.device_type == "multi_usrp":
        #         handler.balance_gain()
        pass 

    def perform_frequency_sweep(self):
        # for handler in self.device_handlers.values():
        #     if handler.device_type == "usrp" or handler.device_type == "multi_usrp":
        #         handler.sweep_frequency()
        pass 

    def update_connection_status(self, device_name, state):
        self.runners[device_name]["state"] = state
        self.device_status_panel.update_device_state(device_name, state)

        inited = True
        for runner in self.runners.values():
            dev_state = runner["state"]
            if dev_state != ConnectionStatus.CONNECTED:
                inited = False
                break

        if inited:
            self.running_status = RunningStatus.STOPPED
            self.connection_status = ConnectionStatus.CONNECTED
        else: 
            # Init failed
            self.running_status = RunningStatus.NOINIT
            self.connection_status = ConnectionStatus.DISCONNECTED
        
        self.update_buttons()

    def update_running_status(self, state):
        self.running_status = state
        self.update_buttons()

    def update_buttons(self):
        self.app_control_panel.update_button_states(
            self.connection_status, self.running_status
        )
        self.experiment_settings_panel.update_button_states(
            self.connection_status, self.running_status
        )

    def handle_time_window_change(self, seconds):
        self.plot_grid.set_display_time(seconds)

    def handle_grid_layout_change(self, rows, cols):
        self.plot_grid.update_grid(rows, cols)

    def handle_add_source(self, source: DataSource):
        if self.plot_grid.add_source(source):
            # Update a
            sel_channels = self.exp_config.get_param("display_sources")
            sel_channels.append(source)
            self.exp_config.set_param("display_sources", list(set(sel_channels)))
            # Change state of UI
            self.experiment_settings_panel.update_source("add", source)

    def handle_remove_source(self, source: DataSource):
        if self.plot_grid.remove_source(source):
            # Update config
            sel_channels = self.exp_config.get_param("display_sources")
            sel_channels.remove(source)
            self.exp_config.set_param("display_sources", sel_channels)
            # Change state of UI
            self.experiment_settings_panel.update_source("remove", source)

    def update_save_state(self, flag):
        self.saving_status = flag

    def toggle_instructions(self, flag):
        self.enable_instructions = flag
        if self.instruction_dialog is not None:
            self.instruction_dialog.toggle_ui(self.enable_instructions)

    def closeEvent(self, a0):
        # Send disconnect to all
        self.disconnect()
        self.listener.stop()
        return super().closeEvent(a0)
