import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from bioview.constants import BIOVIEW_VERSION


class ConfigPromptDialog(QDialog):
    def __init__(self, instructions, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"BioView Device Loader, Version {BIOVIEW_VERSION}")
        self.setModal(True)  # Make it a modal dialog, blocking parent window
        self.selected_files = []  # To store paths of files selected by the user

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # Add some spacing between elements

        # Instructions Label
        instructions_text = (
            "Welcome to BioView Client!\n\n"
            "To proceed, please load your device configuration files.\n"
            "You can select multiple JSON files containing device configurations.\n\n"
            "Click 'Browse...' to select files, or 'Exit' to close the application."
        )
        self.instructions_label = QLabel(instructions_text)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setWordWrap(True)  # Allow text to wrap
        main_layout.addWidget(self.instructions_label)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch(1)  # Push buttons to the center/right

        # Exit Button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedSize(120, 40)  # Fixed size for better appearance
        self.exit_button.clicked.connect(
            self.reject
        )  # QDialog.reject() sets result to QDialog.Rejected
        buttons_layout.addWidget(self.exit_button)

        # Browse Button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setFixedSize(120, 40)
        self.browse_button.clicked.connect(self.open_file_dialog)
        buttons_layout.addWidget(self.browse_button)

        buttons_layout.addStretch(1)  # Push buttons to the center/left
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.setMinimumSize(400, 200)  # Set a minimum size for the dialog

        # Set object name for specific styling
        self.exit_button.setObjectName("exit_button")

    def open_file_dialog(self):
        """Opens a file dialog to select multiple JSON files."""
        # QFileDialog.getOpenFileNames returns a tuple: (list_of_filenames, selected_filter)
        # We only care about the list of filenames.
        # 'JSON Files (*.json);;All Files (*)' defines the file type filter.
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Device Configuration Files",
            os.getcwd(),  # Initial directory
            "JSON Files (*.json);;All Files (*)",
        )

        if files:
            self.selected_files = files
            self.accept()  # QDialog.accept() sets result to QDialog.Accepted
        else:
            # If user opens dialog but selects no files, they can still click 'Exit'
            # or 'Browse...' again. Don't close the dialog automatically here.
            print("No files selected. Try again or exit.")
