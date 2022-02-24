import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from textwrap import dedent

class Worker(QThread):
    def __init__(self, func, args):
        super(Worker, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)

class ConsoleWindowLogHandler(logging.Handler, QObject):
    sigLog = pyqtSignal(str)
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
        self.setFormatter(formatter)

    def emit(self, logRecord):
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