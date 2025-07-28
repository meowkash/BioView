# For some ass-backward reason, both uhd and time are ESSENTIAL for the app to not crash
import logging
import queue
import time
from pathlib import Path

import uhd
from PyQt6.QtCore import QMutex
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QStatusBar, QVBoxLayout, QWidget

from bioview.device import get_device_object
from bioview.device.common import InstructionWorker
from bioview.datatypes import (
    ConnectionStatus,
    DataSource,
    ExperimentConfiguration,
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


class Viewer(QMainWindow):
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

        # Create device handlers
        self.device_handlers = {}
        for dev_name, dev_cfg in device_config.items():
            dev_obj = get_device_object(
                device_name=dev_name,
                config=dev_cfg,
                save=self.saving_status,
                exp_config=exp_config,
            )
            dev_obj.connectionStateChanged.connect(
                lambda value: self.update_connection_status(
                    device=dev_name, state=value
                )
            )
            self.device_handlers[dev_name] = dev_obj
        self.discover_channels()

        # Initialize device states
        self.device_states = {}
        for dev_name in device_config.keys():
            self.device_states[dev_name] = ConnectionStatus.DISCONNECTED

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

        ### Common Threads
        self.instructions_thread = None

        ### Data Queues
        self.usrp_disp_queue = queue.Queue(maxsize=10000)

        # Enable Logging
        self._connect_logging()
        self._connect_display()

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
        self.app_control_panel.connectionInitiated.connect(self.start_initialization)
        self.app_control_panel.startRequested.connect(self.start_recording)
        self.app_control_panel.stopRequested.connect(self.stop_recording)
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
        for handler in self.device_handlers.values():
            if handler.device_type == "multi_usrp":
                usrp_cfg = handler.config.devices.values()

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
        self.device_status_panel = DeviceStatusPanel(self.device_states)
        # Add device status panel to status bar (on the right side)
        self.status_bar.addPermanentWidget(self.device_status_panel)
        # Add some info text to status bar
        self.status_bar.showMessage("Ready")

    def _connect_logging(self):
        self.plot_grid.logEvent.connect(self.log_display_panel.log_message)
        for _, panel in enumerate(self.usrp_config_panel):
            panel.logEvent.connect(self.log_display_panel.log_message)
        for handler in self.device_handlers.values():
            handler.logEvent.connect(self.log_display_panel.log_message)

    def _connect_display(self):
        for handler in self.device_handlers.values():
            handler.dataReady.connect(self.plot_grid.add_new_data)

    def discover_channels(self):
        # Make all sources available to the overall app
        for handler in self.device_handlers.values():
            for source in handler.data_sources:
                self.exp_config.available_channels.append(source)

    def start_initialization(self):
        # Disable button during initialization
        self.running_status = RunningStatus.NOINIT
        self.connection_status = ConnectionStatus.CONNECTING
        self.update_buttons()

        for handler in self.device_handlers.values():
            handler.connect()

        # Make all sources available for display

    def start_recording(self):
        # Update state
        self.running_status = RunningStatus.RUNNING
        self.connection_status = ConnectionStatus.CONNECTED

        for handler in self.device_handlers.values():
            handler.run()

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

    def stop_recording(self):
        # Update state
        self.running_status = RunningStatus.STOPPED
        self.connection_status = ConnectionStatus.CONNECTED

        for handler in self.device_handlers.values():
            handler.stop()

        # Stop instruction
        if self.instructions_thread is not None:
            self.instructions_thread.stop()

        # Update UI
        self.update_buttons()

    def perform_gain_balancing(self):
        for handler in self.device_handlers.values():
            if handler.device_type == "usrp" or handler.device_type == "multi_usrp":
                handler.balance_gain()

    def perform_frequency_sweep(self):
        for handler in self.device_handlers.values():
            if handler.device_type == "usrp" or handler.device_type == "multi_usrp":
                handler.sweep_frequency()

    def update_connection_status(self, device, state):
        self.device_states[device] = state
        self.device_status_panel.update_device_state(device, state)

        inited = True
        for _, dev_state in self.device_states.items():
            if dev_state != ConnectionStatus.CONNECTED:
                inited = False
                break

        if inited:
            self.running_status = RunningStatus.STOPPED
            self.connection_status = ConnectionStatus.CONNECTED
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

    def on_init_failure(self, error_message):
        self.running_status = RunningStatus.NOINIT
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.update_buttons()

        self.log_display_panel.log_message("error", error_message)
        self.usrp = None

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
        # Ensure all threads are closed
        self.stop_recording()
        return super().closeEvent(a0)
