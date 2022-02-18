
from PyQt5.QtCore import QObject, QThread, pyqtSignal

import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)

class AutoDebugThread(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def runAutoDebug(self):
        logger.info('Initializing Debugger...')
        abinDebugger = self.abinDebugger(self.function_name, self.bugged_file_path, self.csvTestSuite, self.max_complexity)
        logger.info('Starting Debugging Process...\n')
        debug_result = abinDebugger.start_auto_debugging()
        logger.info('Debugging Process Finished.\n')
        (model_name, behavior, prev_observation, new_observation) = debug_result
        logger.info(f"Behavior Type: {behavior}")
        logger.info(f"Previous Observations:\n{prev_observation}\n")
        logger.info(f"New Observations:\n{new_observation}\n")
        msgResult = QMessageBox()
        if model_name == '':
            msgTitle = 'UNABLE TO REPAIR!'
            msgText = 'AbinDebugger was unable to repair the provided program.'
        else:
            msgTitle = 'SUCCESSFUL REPAIR!'
            msgText = 'The provided program was successfully repaired.'
            self.debugged_program = model_name
            self.AbductionPage.findChild(QListWidget, 'lstModel').setCurrentRow(abinDebugger.candidate-3)
            self.AbductionPage.findChild(QListWidget, 'lstModel').currentItem().setText(abinDebugger.bugfixing_hyphotesis)
        logger.info(f"{msgTitle}\n")
        msgResult.information(self, msgTitle, msgText)