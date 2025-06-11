from PyQt6.QtCore import QThread

from bioview.types import ExperimentConfiguration


class SaveWorker(QThread):
    def __init__(
        self, config: ExperimentConfiguration, running: bool = False, parent=None
    ):
        super().__init__(parent)

        self.config = config
        self.running = running

    def run(self):
        while self.running:
            pass

    def stop(self):
        self.running = False
