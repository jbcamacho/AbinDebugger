"""
This module is the controller of the system.
This is the controller representation of the MVC software pattern.
"""
from logging import exception
import sys
import builtins
from AbinView import AbinView
from AbinModel import AbinModel
from typing import Tuple, Type
from pathlib import Path
import yaml
import pandas as pd
from pandas import DataFrame
from webbrowser import open as linkOpen
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QFileDialog,
    QTableWidgetItem, QTableWidget, QPushButton,
    QComboBox, QSpinBox, QListWidget, QPlainTextEdit,
    QDoubleSpinBox, QLineEdit, QRadioButton, QGroupBox
)
import controller.DebugController as DebugController
from model.HyphotesisTester import Behavior
from model.HypothesisRefinement import AbductionSchema
from controller.AbinLogging import Worker
from model.misc.test_db_connection import test_db_connection
import model.misc.bug_mining as bug_mining
import controller.AbinLogging as AbinLogging

#Pattern Model-View-Controller
AbInModel = Type[AbinModel]
AbInView = Type[AbinView]
#Controller = Type[AbinDriver]


class AbinDriver(AbinView):
    """ This class is the encapsulation of the controller"""
    def __init__(self, parent=None, abin_debugger: AbInModel = AbinModel):
        """ Constructor Method """
        super().__init__(parent)
        self.defaultFontSize = self.font().pointSize()
        self._connectActions()
        self.csvTestSuite = None
        self.csvTestTypes = None  
        self.bugged_file_path = None
        self.function_name = None
        self.abinDebugger = abin_debugger
        self.max_complexity = 0
        self.debugged_program = None
        self._debug_elapsed_time = 0
        self.csvTestSuite = None
        self.lstRepos = None
        self.abduction_schema = AbductionSchema.DFS
          
    def _connectActions(self):
        """ This method connect all the signals to a QWidget object"""
        # Connect File actions
        self.loadModelAction.triggered.connect(self.loadModel)
        self.loadTestAction.triggered.connect(self.loadTestSuite)
        self.saveAction.triggered.connect(self.saveDebuggedProgram)
        self.exitAction.triggered.connect(self.close)
        
        # Connect View actions
        self.zoomDefaultAction.triggered.connect(lambda: self.setStyleSheet(f"font-size: {self.defaultFontSize}pt;"))
        self.zoomInAction.triggered.connect(lambda: self.setStyleSheet(f"font-size: {self.font().pointSize() + 1}pt;"))
        self.zoomOutAction.triggered.connect(lambda: self.setStyleSheet(f"font-size: {self.font().pointSize() - 1}pt;"))

        # Connect Connection actions
        self.connectAction.triggered.connect(self.testDBConn)

        # Connect Help actions
        self.helpContentAction.triggered.connect(self.contactInfo)
        self.aboutAction.triggered.connect(self.about)
        self.githubAction.triggered.connect(
            lambda: linkOpen("https://github.com/jbcamacho/abin_debugger.git")
        )

        # Connect Left SideBar Actions
        self.homeAction.triggered.connect(self.toHomePage)
        self.commandAction.triggered.connect(self.toTestSuitePage)
        self.abductionAction.triggered.connect(self.toDebuggerPage)
        self.miningAction.triggered.connect(self.toMiningPage)
        self.databaseAction.triggered.connect(self.toDatabasePage)
        self.configAction.triggered.connect(self.toConfigPage)

        # Connect Debugger Page Events
        self.btnRunAutoDebug = self.AbductionPage.findChild(QPushButton, 'btnStartDebug')
        self.btnRunAutoDebug.clicked.connect(self.runAutoDebug)
        self.testSuitePage.findChild(QPushButton, 'btnLoadTestSuite').clicked.connect(self.loadTestSuite)
        self.databasePage.findChild(QPushButton, 'btnConnectDatabase').clicked.connect(self.testDBConn)
        self.miningPage.findChild(QPushButton, 'btnGetRepos').clicked.connect(self.downloadRepos)
        self.miningPage.findChild(QPushButton, 'btnLoadRepos').clicked.connect(lambda: self.loadRepos(''))
        self.miningPage.findChild(QPushButton, 'btnMineRepos').clicked.connect(self.mineRepos)
        self.configPage.findChild(QPushButton, 'btnConfLoad').clicked.connect(self.loadConfigFile)
        self.configPage.findChild(QPushButton, 'btnConfSave').clicked.connect(self.saveConfigFile)
        self.configPage.findChild(QPushButton, 'btnConfDefault').clicked.connect(self.resetConfigFile)
        self.allPages.currentChanged.connect(self._readConfigData)

        ## Connect radiobuttons to onchange.
        gpbSchema = self.AbductionPage.findChild(QGroupBox, 'gpbSchema')
        gpbSchema.findChild(QRadioButton, 'rdbDFS').toggled.connect(self.schemaOnChange)
        gpbSchema.findChild(QRadioButton, 'rdbBFS').toggled.connect(self.schemaOnChange)
        gpbSchema.findChild(QRadioButton, 'rdbAStar').toggled.connect(self.schemaOnChange)

        ## Connect Logger to txtLogging and AutoDebugTask to a thread
        self.AutoDebug = Worker(self.AutoDebugTask, ())
        self.AutoDebug.finished.connect(self.finishedAutoDebug)
        self.AutoDebug.terminate()
        self.txtLogging = self.AbductionPage.findChild(QPlainTextEdit, 'txtLogging')
        AbinLogging.CONSOLE_HANDLER.sigLog.connect(self.txtLogging.appendPlainText)

        ## Connect Logger to txtConnectionStatus
        self.txtConnectionStatus = self.databasePage.findChild(QPlainTextEdit, 'txtConnectionStatus')
        AbinLogging.TEST_DB_HANDLER.sigLog.connect(self.txtConnectionStatus.appendHtml)

        ## Connect Logger to txtMiningLog and miningTask to a thread
        self.miningThread = Worker(self.miningTask, ())
        self.miningThread.finished.connect(self.finishedMineRepos)
        self.miningThread.terminate()
        self.txtMiningLog = self.miningPage.findChild(QPlainTextEdit, 'txtMiningLog')
        AbinLogging.MINING_HANDLER.sigLog.connect(self.txtMiningLog.appendPlainText)

        # Connect Timer for debugging elapsed time
        self.timer.timeout.connect(self._showDebugTime)

    def _showDebugTime(self):
        """ This method show the debug elapsed time in the status bar """
        self._debug_elapsed_time += 1
        self.statusDebugging.setText(f"  Debug in progress... elapsed time: {self._debug_elapsed_time/10} sec(s)  ")

    def _resetDebugTimer(self):
        """ This method resets the debug QTimer """
        self._debug_elapsed_time = 0
        self.timer.start(100)
    
    def _stopDebugTimer(self):
        """ This method stops the debug QTimer """
        self.timer.stop()
        self.statusDebugging.setText(f"  Debugging finished total elapsed time: {self._debug_elapsed_time/10} sec(s)  ")

    def toHomePage(self) -> None:
        """ This method set the QStackedWidget to the QWidget homePage """
        self.allPages.setCurrentWidget(self.homePage)
        self.statusLabel.setText(f"  Home  ")

    def toTestSuitePage(self) -> None:
        """ This method set the QStackedWidget to the QWidget testSuitePage """
        self.allPages.setCurrentWidget(self.testSuitePage)
        self.statusLabel.setText(f"  Test Suite  ")

    def toDebuggerPage(self) -> None:
        """ This method set the QStackedWidget to the QWidget debuggerPage """
        self.allPages.setCurrentWidget(self.AbductionPage)
        self.statusLabel.setText(f"  Debugger  ")
    
    def toMiningPage(self) -> None:
        """ This method set the QStackedWidget to the QWidget miningPage """
        self.allPages.setCurrentWidget(self.miningPage)
        self.statusLabel.setText(f"  Mining  ")

    def toDatabasePage(self) -> None:
        """ This method set the QStackedWidget to the QWidget databasePage """
        self.allPages.setCurrentWidget(self.databasePage)
        self.statusLabel.setText(f"  Database  ")

    def toConfigPage(self) -> None:
        """ This method set the QStackedWidget to the QWidget configPage """
        self.allPages.setCurrentWidget(self.configPage)
        self.statusLabel.setText(f"  Settings  ")

    def contactInfo(self):
        """ This method shows up a messagebox showing the contact info"""
        QMessageBox.about(self,
            "Contact Info",
            "<center>Automatic Debugging of Semantic Bugs in Python Programs Using Abductive Inference</center>"
            "<p>- Juan Camacho (juan.camacho@cinvestav.mx)</p>"
            "<p>- Raul Gonzalez (raul.gonzalez@cinvestav.mx)</p>"
            "<p>- Pedro Mejia (pedro.mejia@cinvestav.mx)</p>",
        )
    
    def about(self):
        """ This method shows up a messagebox showing the about info"""
        QMessageBox.about(self,
            "AbinDebugger V1.0",
            "<center>This software was developed as part of a Master's Thesis.</center>",
        )

    def loadTestSuite(self) -> Tuple[DataFrame, DataFrame]:
        """ This method loads the test suite.
        
        This method will popup a window for the user to select a .csv file
        that corresponds to the test suite of the bugged program.

        : rtype: Tuple[DataFrame, DataFrame]
        """
        def parse_csv_data(data):
            """ This method parses the .csv file into a pandas dataframe """
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
        AbinLogging.debugging_logger.info(f'Loaded Test Suite from {csv_file[0]}')

    def loadModel(self):
        """This method loads the bugged program.
        
        This method will popup a window for the user to select a .py file
        that corresponds to the bugged program.
        """
        def get_all_func_names(module_path) -> list:
            """ This method return all the function names in the bugged program """
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
        AbinLogging.debugging_logger.info(f'Loaded Defective Program from {self.bugged_file_path}')
            
    def saveDebuggedProgram(self) -> bool:
        """ This method saves the repaired program.

        This method will popup a window for the user to select a path
        to save the repaired program.
        
        : rtype: bool
        """
        if self.debugged_program is None:
            return QMessageBox.information(self, 
                "Unable to perform action",
                "<p>There are not debugged programs in the current session.</p>"
            )
        save_path = QFileDialog.getSaveFileName(self, 'Save Python - Repaired Program', 'repaired_program.py')
        if not save_path[0]:
            return 0
        with open(save_path[0], 'w') as f:
            f.write('\n'.join(self.debugged_program))
        return 1

    def runAutoDebug(self):
        """ This method execute the AutoDebugTask in a Qthread """
        if DebugController.DB_STATUS == DebugController.ConnectionStatus.Undefined:
            return QMessageBox.warning(self, "Warning!", "<p>Please connect a Database.</p>")
        if DebugController.DB_STATUS == DebugController.ConnectionStatus.Established:
            return QMessageBox.warning(self, "Warning!", "<p>Please make sure to connect a Database with patterns.</p>")
        if self.csvTestSuite is None:
            return QMessageBox.warning(self, "Warning!", "<p>Please provide a test suite!.</p>")
        if self.bugged_file_path is None:
            return QMessageBox.warning(self, "Warning!", "<p>Please provide a bugged program!.</p>")
        
        self.function_name = self.AbductionPage.findChild(QComboBox, 'cmbTargetFunction').currentText()
        if self.function_name == '':
            return QMessageBox.warning(self, "Warning!", "<p>Please provide a function name!.</p>")
        self.max_complexity = self.AbductionPage.findChild(QSpinBox, 'snbComplexity').value()
        test_timeout = float(self.AbductionPage.findChild(QDoubleSpinBox, 'snbTimeout').value())
        DebugController.TEST_TIMEOUT = test_timeout
        self.btnRunAutoDebug.setEnabled(False)
        self._resetDebugTimer()
        #self.AutoDebugTask()
        #self.finishedAutoDebug()
        self.AutoDebug.start()
    
    def finishedAutoDebug(self):
        """ This method is executed when AutoDebugTask finishes """
        self.btnRunAutoDebug.setEnabled(True)
        self._stopDebugTimer()
        if self.debug_result is not None:
            msgResult = QMessageBox()
            (model_src_code, candidate, bugfixing_hyphotesis, behavior, *_) = self.debug_result

            if model_src_code == '':
                msgTitle = 'UNABLE TO REPAIR!'
                msgText = 'AbinDebugger was unable to repair the provided program.'
            elif behavior == Behavior.Valid:
                msgTitle = 'NO DEFECT FOUND!'
                msgText = 'AbinDebugger did not detect any defects in the provided program.'
            else:
                msgTitle = 'SUCCESSFUL REPAIR!'
                msgText = 'The provided program was successfully repaired.'
                self.debugged_program = model_src_code
                if candidate and bugfixing_hyphotesis:
                    self.AbductionPage.findChild(QListWidget, 'lstModel').clear()
                    self.AbductionPage.findChild(QListWidget, 'lstModel').addItems(model_src_code)
                    self.AbductionPage.findChild(QListWidget, 'lstModel').setCurrentRow(candidate - 1)
                    # self.AbductionPage.findChild(QListWidget, 'lstModel').currentItem().setText(str(bugfixing_hyphotesis))
            AbinLogging.debugging_logger.info(f"{msgTitle}")
            msgResult.information(self, msgTitle, msgText)    

    def AutoDebugTask(self):
        """ This method encapsulates the Automatic Repair of the Bugged Program """
        self.txtLogging.clear()
        self.debug_result = None
        AbinLogging.debugging_logger.info('Initializing Debugger...')
        abinDebugger = self.abinDebugger(self.function_name, 
                                        self.bugged_file_path, 
                                        self.csvTestSuite, 
                                        self.max_complexity, 
                                        self.abduction_schema)
        AbinLogging.debugging_logger.info('Starting Debugging Process...')
        result = abinDebugger.start_auto_debugging()
        AbinLogging.debugging_logger.info('Debugging Process Finalized.')
        (model_name, behavior, prev_observation, new_observation) = result
        AbinLogging.debugging_logger.info(f"""
            Behavior Type: {behavior}
            Previous Observations:
            {prev_observation}
            New Observations:
            {new_observation}
            """
        )
        self.debug_result = (
            model_name, 
            abinDebugger.candidate, 
            abinDebugger.bugfixing_hyphotesis, 
            behavior, 
            prev_observation, 
            new_observation
        )

    def testDBConn(self):
        """ This method establish a connection to the database """
        self.txtConnectionStatus.setPlainText('')
        txtHost = self.databasePage.findChild(QLineEdit, 'txtHost')
        host = txtHost.text()
        if not host:
            host = txtHost.placeholderText()

        txtPort = self.databasePage.findChild(QLineEdit, 'txtPort')
        port = txtPort.text()
        if not port:
            port = txtPort.placeholderText()

        txtDatabase = self.databasePage.findChild(QLineEdit, 'txtDatabase')
        db_name = txtDatabase.text()
        if not db_name:
            db_name = txtDatabase.placeholderText()

        txtCollection = self.databasePage.findChild(QLineEdit, 'txtCollection')
        collection_name = txtCollection.text()
        if not collection_name:
            collection_name = txtCollection.placeholderText()
        
        uri = self.databasePage.findChild(QComboBox, 'cmbURI').currentText()

        conn_status = test_db_connection(uri, host, port, db_name, collection_name)
        DebugController.DB_STATUS = conn_status
        self.statusDatabase.setText(f"  DataBase Connection: {conn_status.name}  ")
        
    def downloadRepos(self) -> bool:
        """ This method encapsulates the task of downloading the repositories to be mined.
        
        : rtype: bool
        """
        spnNoRepos = self.miningPage.findChild(QSpinBox, 'spnNoRepos')
        spnNoRepoPages = self.miningPage.findChild(QSpinBox, 'spnNoRepoPages')
        cmbLanguage = self.miningPage.findChild(QComboBox, 'cmbLanguage')
        lang = cmbLanguage.currentText()
        max_per_page = spnNoRepos.value()
        page_no = spnNoRepoPages.value()
        repositories_data = bug_mining.getTopRepositories(lang, page_no, max_per_page)
        save_path = QFileDialog.getSaveFileName(self, 'Save JSON - Repositories', 'topRepos.json')
        if not save_path[0]:
            return 0
        bug_mining.writeJSONFile(repositories_data, save_path[0])
        self.loadRepos(save_path[0])
        return 1

    def loadRepos(self, file_path: str = '') -> bool:
        """ This method load a .json file that contains the data of the repositories to be mined.
        
        :param file_path: The path to the .json file
        that will be loaded.
        :type  file_path: str
        : rtype: bool
        """
        from json import load
        if file_path:
            repos_file = file_path
        else: 
            repos_file = QFileDialog.getOpenFileName(self, 'Load JSON - Repositories', '', 'JSON(*.json)')
            repos_file = repos_file[0]
        if not repos_file:
            return 0
        with open(repos_file, 'r') as f:
            repositories_data = load(f)
        self.lstRepos = self.miningPage.findChild(QListWidget, 'lstRepos')
        self.lstRepos.clear()
        for i, repo in enumerate(repositories_data):
            owner = repo['owner']
            name = repo['name']
            self.lstRepos.addItem(f"{i+1}\t{owner}/{name}")
        return 1
        
    def mineRepos(self):
        """ This method execute the miningTask in a Qthread """
        if DebugController.DB_STATUS == DebugController.ConnectionStatus.Undefined:
            return QMessageBox.warning(self, "Warning!", "<p>Please connect a Database.</p>")
        if self.lstRepos is None:
            return QMessageBox.warning(self, "Warning!", "<p>Please load the repositories data.</p>")
        self.miningThread.start()

    def finishedMineRepos(self):
        """ This method is executed when miningTask finishes """
        self.statusMining.setText(f"  Mining Process: IDLE  ")

    def miningTask(self):
        """ This method encapsulates the bug mining task """
        txtDatabase = self.miningPage.findChild(QLineEdit, 'txtReposDatabase')
        db_name = txtDatabase.text()
        if not db_name:
            db_name = txtDatabase.placeholderText()

        txtReposCollection = self.miningPage.findChild(QLineEdit, 'txtReposCollection')
        nameReposCollection = txtReposCollection.text()
        if not nameReposCollection:
            nameReposCollection = txtReposCollection.placeholderText()

        txtPatternsCollection = self.miningPage.findChild(QLineEdit, 'txtPatternsCollection')
        namePatternsCollection = txtPatternsCollection.text()
        if not namePatternsCollection:
            namePatternsCollection = txtPatternsCollection.placeholderText()

        from model.HypothesisGenerator import HypothesisGenerator as CONN
        db_connection = CONN.mongodb_connection()
        collection_RepoData = db_connection[nameReposCollection]
        collection_BugPatterns = db_connection[namePatternsCollection]
        
        remaining_repos = self.lstRepos.count()
        AbinLogging.mining_logger.info(
            f"Starting to Mine {remaining_repos} Repositories."
        )
        for i in range(remaining_repos):
            repo_item = self.lstRepos.takeItem(0)
            repo = repo_item.text().split('\t')[1]
            (owner, name) = repo.split('/')
            AbinLogging.mining_logger.info(f"Current repository: {owner}/{name}.")
            self.statusMining.setText(
                f"  Mining {owner}/{name} repository {i + 1} of {remaining_repos}. "
            )
            # check if the repo was not previosly mined
            if len(list(collection_RepoData.find( { "repo": name, "owner": owner} ))) != 0:
                AbinLogging.mining_logger.info(
                    f"The repository {owner}/{name} was previously mined!."
                )
                continue
            AbinLogging.mining_logger.info(
                f"Mining repository {i + 1} of {remaining_repos}."
            )
            process_meta_data = f"Repository: {owner}/{name}."
            (repo_data, bugfixes_data) = bug_mining.mineBugCommitsFromRepo(owner, name, process_meta_data)
            if bugfixes_data:
                insert_result_RepoData = collection_RepoData.insert_one(repo_data.copy())
                insert_result_BugPatterns = collection_BugPatterns.insert_many(bugfixes_data.copy())
            else:
                AbinLogging.mining_logger.info(
                    f"Empty!, No commits were mined from repository {owner}/{name}."
                )

    def stopMineRepos(self):
        """ Abstract Method """
        pass

    def schemaOnChange(self):
        """ This method serves as the toggle event for the radio buttons.
        The value of abduction schema will be changed depending of the selection.
        """
        radioBtn = self.sender()
        if radioBtn.isChecked():
            if radioBtn.text() == 'DFS':
                self.abduction_schema = AbductionSchema.DFS
            elif radioBtn.text() == 'BFS':
                self.abduction_schema = AbductionSchema.BFS
            else:
                self.abduction_schema = AbductionSchema.A_star

    def loadConfigFile(self):
        config_file_path = QFileDialog.getOpenFileName(
            self, 'Load YAML - Configuration File', '', 'YAML(*.yaml *.yml)')
        if config_file_path[0]:
            with open(config_file_path[0], 'r') as config_file:
                config_data = yaml.full_load(config_file)
            self._setConfigData(config_data)
    
    def saveConfigFile(self) -> bool:        
        config_data = self._readConfigData()
        save_path = QFileDialog.getSaveFileName(
            self, 'Save YAML - Configuration File', 'config.yml')
        if save_path[0]:
            save_path = save_path[0]
        else:
            save_path = 'controller/config.yml'
        try:
            with open(save_path, 'w') as config_file:
                yaml.dump(config_data, config_file)   
        except Exception as e:
            print(e)
        else:
            return 1
        return 0

    def resetConfigFile(self):
        self._setConfigData(self.default_config)



def debugger_is_active() -> bool:
    """ This method return if the debugger is currently active """
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