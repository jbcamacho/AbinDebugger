import sys
import builtins
from AbinView import AbinView
from AbinModel import AbinModel
from typing import Type
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QFileDialog,
    QTableWidgetItem, QTableWidget, QPushButton,
    QComboBox, QSpinBox, QListWidget, QPlainTextEdit
)

import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER, Worker
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)

#Pattern Model-View-Controller
AbInModel = Type[AbinModel]
AbInView = Type[AbinView]
#Controller = Type[AbinDriver]


class AbinDriver(AbinView):
    
    def __init__(self, parent=None, abin_debugger: AbInModel = AbinModel):
        super().__init__(parent)
        self._connectActions()
        self.csvTestSuite = None
        self.csvTestTypes = None  
        self.bugged_file_path = None
        self.function_name = None
        self.abinDebugger = abin_debugger
        self.max_complexity = 0
        self.debugged_program = None
        self._debug_elapsed_time = 0
          
    def _connectActions(self):
        # Connect File actions
        self.loadModelAction.triggered.connect(self.loadModel)
        self.loadTestAction.triggered.connect(self.loadTestSuite)
        self.saveAction.triggered.connect(self.saveDebuggedProgram)
        self.exitAction.triggered.connect(self.close)
        # Connect Edit actions
        #self.copyAction.triggered.connect(self.copyContent)
        #self.pasteAction.triggered.connect(self.pasteContent)
        #self.cutAction.triggered.connect(self.cutContent)
        
        # Connect Help actions
        self.helpContentAction.triggered.connect(self.contactInfo)
        self.aboutAction.triggered.connect(self.about)

        # Connect Left SideBar Actions
        self.homeAction.triggered.connect(self.toHomePage)
        self.commandAction.triggered.connect(self.toTestSuitePage)
        self.abductionAction.triggered.connect(self.toDebuggerPage)

        # Connect Debugger Page Events
        self.btnRunAutoDebug = self.AbductionPage.findChild(QPushButton, 'btnStartDebug')
        self.btnRunAutoDebug.clicked.connect(self.runAutoDebug)
        self.testSuitePage.findChild(QPushButton, 'btnLoadTestSuite').clicked.connect(self.loadTestSuite)

        # Connect Logger to txtLogging and AutoDebug to a thread
        self.AutoDebug = Worker(self.AutoDebugTask, ())
        self.AutoDebug.finished.connect(self.finishedAutoDebug)
        self.AutoDebug.terminate()
        self.txtLogging = self.AbductionPage.findChild(QPlainTextEdit, 'txtLogging')
        CONSOLE_HANDLER.sigLog.connect(self.txtLogging.appendPlainText)

        self.timer.timeout.connect(self._showDebugTime)

    def _showDebugTime(self):
        self._debug_elapsed_time += 1
        self.statusLabel.setText(f"Debugging in progress... elapsed time: {self._debug_elapsed_time/10} sec(s)")

    def _resetDebugTimer(self):
        self._debug_elapsed_time = 0
        self.timer.start(100)
    
    def _stopDebugTimer(self):
        self.timer.stop()
        self.statusLabel.setText(f"Debugging finished. Total elapsed time: {self._debug_elapsed_time/10} sec(s)")

    def toHomePage(self) -> None:
        self.allPages.setCurrentWidget(self.homePage)
        self.statusLabel.setText(f"Home")

    def toTestSuitePage(self) -> None:
        self.allPages.setCurrentWidget(self.testSuitePage)
        self.statusLabel.setText(f"Test Suite")

    def toDebuggerPage(self) -> None:
        self.allPages.setCurrentWidget(self.AbductionPage)
        self.statusLabel.setText(f"Debugger")

    def contactInfo(self):
        QMessageBox.about(self,
            "Contact Info",
            "<center>Automatic Debugging of Semantic Bugs in Python Programs Using Abductive Inference</center>"
            "<p>- Juan Camacho (juan.camacho@cinvestav.mx)</p>"
            "<p>- Raul Gonzalez (raul.gonzalez@cinvestav.mx)</p>"
            "<p>- Pedro Mejia (pedro.mejia@cinvestav.mx)</p>",
        )
    
    def about(self):
        QMessageBox.about(self,
            "AbinDebugger V1.0",
            "<center>This software was developed as part of a Master's Thesis.</center>",
        )

    def loadTestSuite(self):
        def parse_csv_data(data):
            from json import loads
            parsed_data = pd.DataFrame()
            parsed_types = []
            columnsNames = list(data.columns)
            parsed_data[columnsNames[0]] = data[columnsNames[0]] # test_cases
            parsed_data[columnsNames[1]] = data[columnsNames[1]] # expected_output
            columnsNames = columnsNames[2:] # skip test_cases and expected_output columns
            for colName in columnsNames:
                newColName, castType = map(str.strip, colName.split(':'))
                parsed_types.append({ 'input_args': newColName, 'type': castType })
                if castType in ['int', 'float', 'str']:
                    parsed_data[newColName] = data[colName].map(getattr(builtins, castType))
                elif castType in ['dict', 'json']:
                    parsed_data[newColName] = data[colName].apply(loads)
                elif castType == 'list':
                    parsed_data[newColName] = data[colName].to_list()
                elif castType == 'tuple':
                    parsed_data[newColName] = tuple(data[colName].to_list())
            return (parsed_data, pd.DataFrame(parsed_types))
        
        csv_file = QFileDialog.getOpenFileName(self, 'Open CSV - TestSuite', '', 'CSV(*.csv)')
        if csv_file[0] == '': return
        df = pd.read_csv(csv_file[0], keep_default_na=False)
        (parsed_data, parsed_types) = parse_csv_data(df)
        self.csvTestSuite = parsed_data
        tableTestSuite = self.testSuitePage.findChild(QTableWidget, 'tableTestSuite')
        numRows = len(self.csvTestSuite.index)
        namesColumns = self.csvTestSuite.columns
        numColumns = len(namesColumns)
        tableTestSuite.setRowCount(numRows)
        tableTestSuite.setColumnCount(numColumns)
        tableTestSuite.setHorizontalHeaderLabels(namesColumns)
        [tableTestSuite.setItem(i, j, QTableWidgetItem(str(self.csvTestSuite.iat[i,j]))) for i in range(numRows) for j in range(numColumns)]
        tableTestSuite.resizeColumnsToContents()
        
        self.csvTestTypes = parsed_types
        tabletypes = self.testSuitePage.findChild(QTableWidget, 'tableTypes')
        numRows = len(self.csvTestTypes.index)
        namesColumns = self.csvTestTypes.columns
        numColumns = len(namesColumns)
        tabletypes.setRowCount(numRows)
        tabletypes.setColumnCount(numColumns)
        tabletypes.setHorizontalHeaderLabels(namesColumns)
        [tabletypes.setItem(i, j, QTableWidgetItem(str(self.csvTestTypes.iat[i,j]))) for i in range(numRows) for j in range(numColumns)]
        tabletypes.resizeColumnsToContents()
        logger.info(f'Loaded Test Suite from {csv_file[0]}\n')

    def loadModel(self):
        def get_all_func_names(module_path) -> list:
            from importlib.util import spec_from_file_location, module_from_spec
            from inspect import getmembers, isfunction, ismethod
            file = module_path.split('/')[-1]
            spec = spec_from_file_location(file, module_path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            return [func_name for func_name, _ in getmembers(module, isfunction or ismethod)]
        file_name = QFileDialog.getOpenFileName(self, 'Open Bugged File - Model', '', 'Python(*.py)')
        self.bugged_file_path = file_name[0]
        bugged_src_code = ''
        if self.bugged_file_path == '': return
        with open(self.bugged_file_path, 'r') as f:
            bugged_src_code = f.readlines()
            file_name = f.name
        self.AbductionPage.findChild(QListWidget, 'lstModel').clear()
        self.AbductionPage.findChild(QListWidget, 'lstModel').addItems(bugged_src_code)
        func_names = get_all_func_names(self.bugged_file_path)
        self.AbductionPage.findChild(QComboBox, 'cmbTargetFunction').clear()
        self.AbductionPage.findChild(QComboBox, 'cmbTargetFunction').addItems(func_names)
        logger.info(f'Loaded Defective Program from {self.bugged_file_path}\n')
            
    def saveDebuggedProgram(self):
        if self.debugged_program is None:
            return QMessageBox.information(self, 
                "Unable to perform action",
                "<p>There are not debugged programs in the current session.</p>"
            )
        from pathlib import Path
        curr_dir = Path(__file__).parent.resolve()
        newest_debugged_path = curr_dir.joinpath("temp", self.debugged_program)
        with open(newest_debugged_path, 'r') as f:
            newest_debugged_model = f.read()
        save_path = QFileDialog.getSaveFileName(self, 'Save File', 'repaired_program.py')
        with open(save_path[0], 'w') as f:
            f.write(newest_debugged_model)
        return save_path

    def runAutoDebug(self):
        if self.csvTestSuite is None:
            return QMessageBox.warning(self, "Warning!", "<p>Please provide a test suite!.</p>")
        if self.bugged_file_path is None:
            return QMessageBox.warning(self, "Warning!", "<p>Please provide a bugged program!.</p>")
        
        self.function_name = self.AbductionPage.findChild(QComboBox, 'cmbTargetFunction').currentText()
        if self.function_name == '':
            return QMessageBox.warning(self, "Warning!", "<p>Please provide a function name!.</p>")
        self.max_complexity = self.AbductionPage.findChild(QSpinBox, 'snbComplexity').value()
        self.btnRunAutoDebug.setEnabled(False)
        self._resetDebugTimer()
        self.AutoDebug.start()
        #self.AutoDebugTask()
        #self.finishedAutoDebug()
    
    def finishedAutoDebug(self):
        self.btnRunAutoDebug.setEnabled(True)
        self._stopDebugTimer()
        if self.debug_result is not None:
            msgResult = QMessageBox()
            (model_name, candidate, bugfixing_hyphotesis, *_) = self.debug_result

            if model_name == '':
                msgTitle = 'UNABLE TO REPAIR!'
                msgText = 'AbinDebugger was unable to repair the provided program.'
            else:
                msgTitle = 'SUCCESSFUL REPAIR!'
                msgText = 'The provided program was successfully repaired.'
                self.debugged_program = model_name
                if candidate and bugfixing_hyphotesis:
                    self.AbductionPage.findChild(QListWidget, 'lstModel').setCurrentRow(candidate - 3)
                    self.AbductionPage.findChild(QListWidget, 'lstModel').currentItem().setText(bugfixing_hyphotesis)
            logger.info(f"{msgTitle}\n")
            msgResult.information(self, msgTitle, msgText)    

    def AutoDebugTask(self):
        self.txtLogging.clear()
        self.debug_result = None
        logger.info('Initializing Debugger...')
        abinDebugger = self.abinDebugger(self.function_name, self.bugged_file_path, self.csvTestSuite, self.max_complexity)
        logger.info('Starting Debugging Process...\n')
        result = abinDebugger.start_auto_debugging()
        logger.info('Debugging Process Finalized.\n')
        (model_name, behavior, prev_observation, new_observation) = result
        logger.info(f"Behavior Type: {behavior}")
        logger.info(f"Previous Observations:\n{prev_observation}\n")
        logger.info(f"New Observations:\n{new_observation}\n")
        self.debug_result = (model_name, abinDebugger.candidate, abinDebugger.bugfixing_hyphotesis, behavior, prev_observation, new_observation)





def debugger_is_active() -> bool:
    """Return if the debugger is currently active"""
    gettrace = getattr(sys, 'gettrace', lambda : None) 
    return gettrace() is not None

if __name__ == "__main__":
    if debugger_is_active():
        print('The program is currenly being execute in debug mode.')
    else:
        app = QApplication(sys.argv)
        win = AbinDriver()
        win.show()
        sys.exit(app.exec_())