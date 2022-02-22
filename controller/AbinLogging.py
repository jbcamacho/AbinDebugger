import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal

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
        message = str(logRecord.getMessage())
        self.sigLog.emit(message)

logger = logging.getLogger(__name__)
LOGGER_LEVEL = logging.INFO
CONSOLE_HANDLER = ConsoleWindowLogHandler()
TEST_DB_HANDLER = ConsoleWindowLogHandler()
logger.addHandler(CONSOLE_HANDLER)