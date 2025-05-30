import pygame
import time
from pathlib import Path

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal

from zapp.types import ExperimentConfiguration

class AudioPlayer(QObject):
    def __init__(self, 
                 config: ExperimentConfiguration, 
                 parent=None
    ):
        super().__init__(parent=parent)
        pygame.mixer.init()
        self.instruction_file = config.get_param('instruction_file', None)
        if self.instruction_file is None or not Path(self.instruction_file).exists(): 
            raise Exception('No valid audio file found.')
        
        self.loop_instruction = config.get_param('loop_instructions', True)
        
        self.running = False
    
    def pre_run(self): 
        try:
            pygame.mixer.music.load(self.instruction_file)
        except Exception as e:
            print(f"Error loading audio file: {e}")
                
    def run(self):
        try:
            while True:
                pygame.mixer.music.play()
                
                # Wait for audio to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
                if not self.loop_instruction: 
                    break
        except Exception as e:
            print(f"Error playing audio: {e}")
            
    def stop(self):
        pygame.mixer.music.stop()

class TextInstruction(QDialog):
    # Popup dialog that displays text instructions like a teleprompter
    def __init__(self, 
                 config: ExperimentConfiguration, 
                 parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle('Instructions')
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        # Setup UI
        layout = QVBoxLayout()
        
        self.text_display = QLabel()
        self.text_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_display.setWordWrap(True)
        self.text_display.setStyleSheet("""
            QLabel {
                padding: 20px;
                font-size: 16px;
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(self.text_display)
        self.setLayout(layout)
        
        # Timer for text progression
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.run)
        
        self.loop_instruction = config.get_param('loop_instructions', True)
        
        # Load instruction from config 
        instruction_file = config.get_param('instruction_file', '')
        if not Path(instruction_file).exists():
            raise Exception('Instruction file does not exist')
        self.instructions = []
        self.instructions = open(instruction_file).read().splitlines()
        
        self.current_index = 0
        self.interval = config.get_param('instruction_interval', 5000)  # 5 seconds default
        
    def pre_run(self):
        self.current_index = 0
        # self.timer.start(self.interval)
            
    def run(self):
        if len(self.instructions) == 0:
            return 
        elif self.current_index >= len(self.instructions): 
            if self.loop_instruction: 
                self.current_index = 0
            else:
                return 
        
        self.text_display.setText(self.instructions[self.current_index])
        time.sleep(self.interval)
        self.current_index += 1
                
    def stop(self):
        # self.timer.stop()
        self.text_display.setText('End of instructions.')
        
class InstructionsWorker(QThread):
    logEvent = pyqtSignal(str, str)
    
    def __init__(self, 
                 config: ExperimentConfiguration, 
                 running: bool = False,
                 parent = None
    ):
        super().__init__(parent)
        self.config = config

        self.instruction_handler = None 
        
        try: 
            if config.get_param('instruction_type') == 'audio': 
                self.instruction_handler = AudioPlayer(config)
            elif config.get_param('instruction_type') == 'text': 
                self.instruction_handler = TextInstruction(config)
        except Exception as e: 
            self.logEvent.emit('error', f'Unable to initialize instruction handler: {e}')
            
        self.running = running 
        
    def run(self):
        if self.instruction_handler == None: 
            self.logEvent.emit('warning', 'No instruction handler available')
            return          
        
        # Initial init
        if getattr(self.instruction_handler, 'pre_run', None) is not None: 
            self.instruction_handler.pre_run() 
        
        while self.running: 
            self.instruction_handler.run()

        # Finally, stop
        self.instruction_handler.stop()
        
    def stop(self):
        self.running = False 
            