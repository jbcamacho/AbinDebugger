"""
This module defines the logging and thread handlers 
to execute long tasks (debugging and mining).
"""
import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from textwrap import dedent
from types import FunctionType
from typing import Any

class Worker(QThread):
    """ This class is a wrapper to execute long tasks in a thread"""
    func: FunctionType
    args: Any
    def __init__(self, func: FunctionType, args: Any) -> None:
        """Contructor Method"""
        super(Worker, self).__init__()
        self.func = func
        self.args = args

    def run(self) -> None:
        """ This method is a wrapper to execute the provided function"""
        self.func(*self.args)

class ConsoleWindowLogHandler(logging.Handler, QObject):
    """ This class provides the handling for logging"""
    sigLog: pyqtSignal = pyqtSignal(str)
    def __init__(self) -> None:
        """Contructor Method"""
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, logRecord: logging.LogRecord) -> str:
        """ This method emit the sigLog signal.

        The emitted signal will be caught by the handler listener
        in the UI and put the logrecord in the QtWidgets.QPlainTextEdit

        :param logRecord: Contains all the information
        pertinent to the event being logged.
        :type  logRecord: logging.LogRecord
        :rtype: str
        """
        message = dedent(str(logRecord.getMessage()))
        self.sigLog.emit(message)

LOGGER_LEVEL = logging.INFO

CONSOLE_HANDLER = ConsoleWindowLogHandler()
debugging_logger = logging.getLogger('DebuggingLogger')
debugging_logger.setLevel(LOGGER_LEVEL)
debugging_logger.addHandler(CONSOLE_HANDLER)

TEST_DB_HANDLER = ConsoleWindowLogHandler()
dbConnection_logger = logging.getLogger('DBConnLogger')
dbConnection_logger.setLevel(LOGGER_LEVEL)
dbConnection_logger.addHandler(TEST_DB_HANDLER)

MINING_HANDLER = ConsoleWindowLogHandler()
mining_logger = logging.getLogger('MiningLogger')
mining_logger.setLevel(LOGGER_LEVEL)
mining_logger.addHandler(MINING_HANDLER)