import sys
from typing import Dict
this = sys.modules[__name__]
this.TIMEOUT_SIGNAL_RECEIVED = 0

from enum import Enum
class ConnectionStatus(Enum):
    Undefined = 0
    Secured = 1
    Established = 2

DATABASE_SETTINGS: Dict[str, str] = {
    'URI': '',
    'HOST': '',
    'PORT': '',
    'DATABASE': '',
    'COLLECTION': '',
    'STATUS': ConnectionStatus.Undefined
}


import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)

def test_timeout_handler(signum, frame):
    this.TIMEOUT_SIGNAL_RECEIVED = 1
    log_entry = f"""Timeout reached!.
    Debug Signal changed to: {this.TIMEOUT_SIGNAL_RECEIVED}.
    Signal handler called with signal {signum}.
    """
    print(log_entry)
    logger.info(log_entry)