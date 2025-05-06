class PORCError(Exception):
    pass

class ValidationError(PORCError):
    pass

class TFEServiceError(PORCError):
    def __init__(self, status_code, message):
        super().__init__(f"TFE API Error ({status_code}): {message}")