"""
PORC Error Classes: Custom exceptions for the PORC system.
"""
import logging
import sys
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'name': record.name,
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

class PORCError(Exception):
    """Base exception for all PORC errors."""
    pass

class ValidationError(PORCError):
    """Raised when validation of input or data fails."""
    pass

class TFEServiceError(PORCError):
    """Raised when a Terraform Enterprise API call fails."""
    def __init__(self, status_code, message):
        super().__init__(f"TFE API Error ({status_code}): {message}")