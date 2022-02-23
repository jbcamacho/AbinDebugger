import sys
import builtins
from AbinView import AbinView
from AbinModel import AbinModel
from typing import Type
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QFileDialog,
    QTableWidgetItem, QTableWidget, QPushButton,
    QComboBox, QSpinBox, QListWidget, QPlainTextEdit,
    QTextEdit, QLineEdit
)
import controller.DebugController as DebugController
from controller.AbinLogging import Worker
from model.misc.test_db_connection import test_db_connection
import model.misc.bug_mining as bug_mining
import controller.AbinLogging as AbinLogging
from controller.DebugController import ConnectionStatus

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
        self.csvTestSuite = None
        self.lstRepos = None
          
    def _connectActions(self):
        # Connect File actions
        self.loadModelAction.triggered.connect(self.loadModel)
        self.loadTestAction.triggered.connect(self.loadTestSuite)
        self.saveAction.triggered.connect(self.saveDebuggedProgram)
        self.exitAction.triggered.connect(self.close)
        
        # Connect Help actions
        self.helpContentAction.triggered.connect(self.contactInfo)
        self.aboutAction.triggered.connect(self.about)

        # Connect Left SideBar Actions
        self.homeAction.triggered.connect(self.toHomePage)
        self.commandAction.triggered.connect(self.toTestSuitePage)
        self.abductionAction.triggered.connect(self.toDebuggerPage)
        self.miningAction.triggered.connect(self.toMiningPage)
        self.databaseAction.triggered.connect(self.toDatabasePage)

        # Connect Debugger Page Events
        self.btnRunAutoDebug = self.AbductionPage.findChild(QPushButton, 'btnStartDebug')
        self.btnRunAutoDebug.clicked.connect(self.runAutoDebug)
        self.testSuitePage.findChild(QPushButton, 'btnLoadTestSuite').clicked.connect(self.loadTestSuite)
        self.databasePage.findChild(QPushButton, 'btnConnectDatabase').clicked.connect(self.testDBConn)
        self.miningPage.findChild(QPushButton, 'btnGetRepos').clicked.connect(self.downloadRepos)
        self.miningPage.findChild(QPushButton, 'btnLoadRepos').clicked.connect(lambda: self.loadRepos(''))
        self.miningPage.findChild(QPushButton, 'btnMineRepos').clicked.connect(self.mineRepos)

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
        self._debug_elapsed_time += 1
        self.statusDebugging.setText(f"  Debug in progress... elapsed time: {self._debug_elapsed_time/10} sec(s)  ")

    def _resetDebugTimer(self):
        self._debug_elapsed_time = 0
        self.timer.start(100)
    
    def _stopDebugTimer(self):
        self.timer.stop()
        self.statusDebugging.setText(f"  Debugging finished total elapsed time: {self._debug_elapsed_time/10} sec(s)  ")

    def toHomePage(self) -> None:
        self.allPages.setCurrentWidget(self.homePage)
        self.statusLabel.setText(f"  Home  ")

    def toTestSuitePage(self) -> None:
        self.allPages.setCurrentWidget(self.testSuitePage)
        self.statusLabel.setText(f"  Test Suite  ")

    def toDebuggerPage(self) -> None:
        self.allPages.setCurrentWidget(self.AbductionPage)
        self.statusLabel.setText(f"  Debugger  ")
    
    def toMiningPage(self) -> None:
        self.allPages.setCurrentWidget(self.miningPage)
        self.statusLabel.setText(f"  Mining  ")

    def toDatabasePage(self) -> None:
        self.allPages.setCurrentWidget(self.databasePage)
        self.statusLabel.setText(f"  Database  ")

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
        AbinLogging.debugging_logger.info(f'Loaded Test Suite from {csv_file[0]}\n')

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
        AbinLogging.debugging_logger.info(f'Loaded Defective Program from {self.bugged_file_path}\n')
            
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
        save_path = QFileDialog.getSaveFileName(self, 'Save Python - Repaired Program', 'repaired_program.py')
        if not save_path[0]:
            return 0
        with open(save_path[0], 'w') as f:
            f.write(newest_debugged_model)
        return 1

    def runAutoDebug(self):
        if DebugController.DATABASE_SETTINGS['STATUS'] == DebugController.ConnectionStatus.Undefined:
            return QMessageBox.warning(self, "Warning!", "<p>Please connect a Database.</p>")
        if DebugController.DATABASE_SETTINGS['STATUS'] == DebugController.ConnectionStatus.Established:
            return QMessageBox.warning(self, "Warning!", "<p>Please make sure to connect a Database with patterns.</p>")
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
        #self.AutoDebugTask()
        #self.finishedAutoDebug()
        self.AutoDebug.start()
    
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
            AbinLogging.debugging_logger.info(f"{msgTitle}\n")
            msgResult.information(self, msgTitle, msgText)    

    def AutoDebugTask(self):
        self.txtLogging.clear()
        self.debug_result = None
        AbinLogging.debugging_logger.info('Initializing Debugger...')
        abinDebugger = self.abinDebugger(self.function_name, self.bugged_file_path, self.csvTestSuite, self.max_complexity)
        AbinLogging.debugging_logger.info('Starting Debugging Process...\n')
        result = abinDebugger.start_auto_debugging()
        AbinLogging.debugging_logger.info('Debugging Process Finalized.\n')
        (model_name, behavior, prev_observation, new_observation) = result
        AbinLogging.debugging_logger.info(f"Behavior Type: {behavior}")
        AbinLogging.debugging_logger.info(f"Previous Observations:\n{prev_observation}\n")
        AbinLogging.debugging_logger.info(f"New Observations:\n{new_observation}\n")
        self.debug_result = (model_name, abinDebugger.candidate, abinDebugger.bugfixing_hyphotesis, behavior, prev_observation, new_observation)

    def testDBConn(self):
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

        DebugController.DATABASE_SETTINGS = {
            'URI': uri,
            'HOST': host,
            'PORT': port,
            'DATABASE': db_name,
            'COLLECTION': collection_name,
            'STATUS':  False
        }
        conn_status = test_db_connection(uri, host, port, db_name, collection_name)
        DebugController.DATABASE_SETTINGS['STATUS'] = conn_status
        self.statusDatabase.setText(f"  DataBase Connection: {conn_status.name}  ")
        
    def downloadRepos(self) -> bool:
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
        if DebugController.DATABASE_SETTINGS['STATUS'] == DebugController.ConnectionStatus.Undefined:
            return QMessageBox.warning(self, "Warning!", "<p>Please connect a Database.</p>")
        if self.lstRepos is None:
            return QMessageBox.warning(self, "Warning!", "<p>Please load the repositories data.</p>")
        self.miningThread.start()

    def finishedMineRepos(self):
        self.statusMining.setText(f"  Mining Process: IDLE  ")

    def miningTask(self):
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
        config = DebugController.DATABASE_SETTINGS
        db_connection = CONN.mongodb_connection()
        collection_RepoData = db_connection[nameReposCollection]
        collection_BugPatterns = db_connection[namePatternsCollection]
        
        remaining_repos = self.lstRepos.count()
        AbinLogging.mining_logger.info(f"Starting to Mine {remaining_repos} Repositories.\n")
        for i in range(remaining_repos):
            repo_item = self.lstRepos.takeItem(0)
            repo = repo_item.text().split('\t')[1]
            (owner, name) = repo.split('/')
            AbinLogging.mining_logger.info(f"Current repository: {owner}/{name}.")
            self.statusMining.setText(f"  Mining {owner}/{name} repository {i + 1} of {remaining_repos}. ")
            # check if the repo was not previosly mined
            if len(list(collection_RepoData.find( { "repo": name, "owner": owner} ))) != 0:
                AbinLogging.mining_logger.info(f"The repository {owner}/{name} was previously mined!.\n")
                continue
            AbinLogging.mining_logger.info(f"Mining repository {i + 1} of {remaining_repos}.\n")
            process_meta_data = f"Repository: {owner}/{name}."
            (repo_data, bugfixes_data) = bug_mining.mineBugCommitsFromRepo(owner, name, process_meta_data)
            if bugfixes_data:
                insert_result_RepoData = collection_RepoData.insert_one(repo_data.copy())
                insert_result_BugPatterns = collection_BugPatterns.insert_many(bugfixes_data.copy())
            else:
                AbinLogging.mining_logger.info(f"Empty!, No commits were mined from repository {owner}/{name}.")

    def stopMineRepos(self):
        pass



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