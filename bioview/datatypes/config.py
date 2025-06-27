class Configuration:
    def __init__(self):
        pass 

    def get_disp_freq(self):
        return 10  # Dummy output

    def set_param(self, param, value): 
        # Ensure we match types
        current_type = type(getattr(self, param, None))
        if current_type is not None:
            setattr(self, param, current_type(value))
        else:
            setattr(self, param, value)

    def get_param(self, param, default_value=None):
        try:
            value = getattr(self, param)
        except AttributeError:
            value = default_value
        
        return value
    