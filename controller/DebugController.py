"""
This module contains global variables necesary for the threaded execution of
the program. Also contains the settings used across the modules.
"""
import sys
from pathlib import Path
from typing import Dict
this = sys.modules[__name__]
this.TIMEOUT_SIGNAL_RECEIVED = 0

MAIN_DIR = Path(__file__).parent.resolve()
WORKING_DIR = MAIN_DIR.joinpath('temp')

from enum import Enum
class ConnectionStatus(Enum):
    Undefined = 0
    Secured = 1
    Established = 2

APP_SETTINGS: Dict[str, str] = {}

DB_STATUS = ConnectionStatus.Undefined

TEST_TIMEOUT: int = int(1)

from controller.pyqtSignalQueue import pyqtSignalQueueHandler
QT_QUEUE = pyqtSignalQueueHandler()

import controller.AbinLogging as AbinLogging

def test_timeout_handler(signum: int, frame) -> None:
    """ The timeout handler.
    
    This function triggers the change of the control variable
    <TIMEOUT_SIGNAL_RECEIVED> in order to raise a timeout exception
    in the AbinCollector class.
    """
    this.TIMEOUT_SIGNAL_RECEIVED = 1
    AbinLogging.debugging_logger.info("Current test timeout reached!")
    AbinLogging.debugging_logger.debug(f"""
        Debug Signal changed to: {this.TIMEOUT_SIGNAL_RECEIVED}.
        Signal handler called with signal {signum}.
        """
    )