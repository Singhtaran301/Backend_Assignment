import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logger(name: str):
    logger = logging.getLogger(name)
    
    # Prevent duplicate logs if already set up
    if logger.hasHandlers():
        return logger
        
    handler = logging.StreamHandler(sys.stdout)
    
    # FORMAT: JSON Structure
    # We include 'trace_id' for correlation (Phase 16 requirement)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger