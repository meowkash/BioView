from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QStatusBar, QVBoxLayout, QWidget

from bioview.datatypes import ConnectionStatus, RunningStatus, ExperimentConfiguration
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

class VisualizerClient(QMainWindow):
    def __init__(
        self,
        device_config: dict,
        exp_config: ExperimentConfiguration,
    ):
        super().__init__()
        
        self.exp_config = exp_config
        self.device_config = device_config

        self.exp_config.available_channels = []

        # Track state
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.running_status = RunningStatus.NOINIT
        self.saving_status = False

        # Track instruction
        if exp_config.get_param("instruction_type") is None:
            self.enable_instructions = False
        else:
            self.enable_instructions = True

        self.instruction_dialog = None
        if exp_config.get_param("instruction_type") == "text":
            self.instruction_dialog = TextDialog()

        # Set up UI
        self.init_ui()
        self.setup_client()
        ### Common Threads
        self.instructions_thread = None

        ### Data Queues
        self.usrp_disp_queue = queue.Queue(maxsize=10000)

        # Enable Logging
        self._connect_logging()
        self._connect_display()
    
    def init_ui(self):
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

    def setup_client(self):
        pass 
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = VisualizerClient()
    window.show()
    
    # Add startup messages
    window.log_panel.add_log_message("info", f"Welcome to BioView Device Discovery Version {BIOVIEW_VERSION}")
    window.log_panel.add_log_message("warning", "Make sure a compatible backend server is running!")
    
    sys.exit(app.exec())