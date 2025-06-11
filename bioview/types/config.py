from PyQt6.QtCore import QMutex


class Configuration:
    def __init__(self):
        # Add mutex to make updates thread safe
        self.mutex = QMutex()

    def set_param(self, param, value):
        self.mutex.lock()
        # Ensure we match types
        current_type = type(getattr(self, param, None))
        if current_type is not None:
            setattr(self, param, current_type(value))
        else:
            setattr(self, param, value)
        self.mutex.unlock()

    def get_param(self, param, default_value=None):
        self.mutex.lock()
        try:
            value = getattr(self, param)
        except:
            value = default_value
        self.mutex.unlock()
        return value
