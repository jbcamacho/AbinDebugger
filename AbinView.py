"""
This module is the view of the system.
This is the view representation of the MVC software pattern.
"""
import sys
from typing import Dict
import resources.qrc_resources as qrc_resources
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5 import sip, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, 
    QToolBar, QAction, QVBoxLayout, QFrame,
    QStackedWidget, QWidget, QTableWidget,
    QTableWidgetItem, QDoubleSpinBox, QLineEdit,
    QComboBox
)
from controller.DebugController import ConnectionStatus
import controller.DebugController as DebugController
from pathlib import Path
import yaml

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
class AbinDebuggerPages(QStackedWidget):
    """ This class loads the pages' UI """
    def __init__(self, parent = None):
        """ Constructor Method """
        QStackedWidget.__init__(self, parent)
        uic.loadUi('view/AbinDebuggerPages.ui', self)
class VLine(QFrame):
    """ This class creates a simple VLine.
    The VLine is used to separate the status bar labels."""
    def __init__(self):
        """ Constructor Method """
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine|self.Sunken)
class AbinView(QMainWindow):
    """ This class is the encapsulation of the view"""
    def __init__(self, parent=None):
        """ Constructor Method """
        super().__init__(parent)
        self.setWindowTitle("Abin Debugger")
        self.setWindowIcon(QIcon(":radar.png"))
        self.resize(1000, 800)
        self._setupUI()
    
    def _setupUI(self):
        """ This method set-ups the UI"""
        self.centralWidget = QFrame()
        self.setCentralWidget(self.centralWidget)
        self._resetLayout()

        self.allPages = AbinDebuggerPages(self.centralWidget)
        self.mainLayout.addWidget(self.allPages)
        self.homePage = self.allPages.findChild(QWidget, 'homePage')
        self.testSuitePage = self.allPages.findChild(QWidget, 'testSuitePage')
        self.AbductionPage = self.allPages.findChild(QWidget, 'abductionPage')
        self.miningPage = self.allPages.findChild(QWidget, 'miningPage')
        self.databasePage = self.allPages.findChild(QWidget, 'databasePage')
        self.configPage = self.allPages.findChild(QWidget, 'configPage')
        self.statsPage = self.allPages.findChild(QWidget, 'statsPage')
        self.testSuitePage.findChild(QTableWidget, 'tableTestSuite').horizontalHeader().setVisible(True)
        self.testSuitePage.findChild(QTableWidget, 'tableTypes').horizontalHeader().setVisible(True)
        
        
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        self._createStatusBar()
        self._createCharts()

        self.configTable = self.configPage.findChild(QTableWidget, 'tableProgramConf')
        self.configTable.sortItems(0, Qt.AscendingOrder)
        self.default_config = self._readConfigData()
        self._loadConfig()

    def _createCharts(self):
        """ This method creates the UI's charts"""
        widgetChartAbduction = self.AbductionPage.findChild(QWidget, 'widgetChartAbduction')
        self.figureAbduction, self.axAbduction = plt.subplots(1, 1)
        # self.axAbduction.plot([],[])
        self.canvasAbduction = FigureCanvas(self.figureAbduction)
        self.canvasAbductionToolbar = NavigationToolbar(self.canvasAbduction, widgetChartAbduction)

        chartAbductionLayout = widgetChartAbduction.layout()
        chartAbductionLayout.addWidget(self.canvasAbductionToolbar)
        chartAbductionLayout.addWidget(self.canvasAbduction)


        widgetChartStats = self.statsPage.findChild(QWidget, 'widgetChartStats')
        self.figureStats, axStats = plt.subplots(1, 2)
        self.axBugs = axStats[0]
        self.axFixes = axStats[1]
        # self.axBugs.plot([],[])
        # self.axFixes.plot([],[])
        self.canvasStats = FigureCanvas(self.figureStats)
        self.canvasStatsToolbar = NavigationToolbar(self.canvasStats, widgetChartStats)

        chartStatsLayout = widgetChartStats.layout()
        chartStatsLayout.addWidget(self.canvasStatsToolbar)
        chartStatsLayout.addWidget(self.canvasStats)

    def _createMenuBar(self):
        """ This method creates the UI's menu bar"""
        menuBar = self.menuBar()
        
        #fileMenu = menuBar.addMenu(QIcon(":menu.svg"), "&Menu")
        fileMenu = menuBar.addMenu("&Menu")
        fileMenu.addAction(self.loadModelAction)
        fileMenu.addAction(self.loadTestAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        viewMenu = menuBar.addMenu("&View")
        viewMenu.addAction(self.zoomDefaultAction)
        viewMenu.addAction(self.zoomInAction)
        viewMenu.addAction(self.zoomOutAction)

        databaseMenu = menuBar.addMenu("&Connection")
        databaseMenu.addAction(self.connectAction)
        # editMenu.addSeparator()

        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.helpContentAction)
        helpMenu.addAction(self.aboutAction)
        helpMenu.addAction(self.githubAction)

    def _createStatusBar(self):
        """ This method creates the UI's status bar"""
        self.statusbar = self.statusBar()
                
        self.statusLabel = QLabel()
        self.statusLabel.setText(f"  Home  ")
        self.statusDebugging = QLabel()
        self.statusDebugging.setText(f"  Debug Process: IDLE  ")
        self.statusDatabase = QLabel()
        self.statusDatabase.setText(f"  DataBase Connection: {ConnectionStatus.Undefined.name}  ")
        self.statusMining = QLabel()
        self.statusMining.setText(f"  Mining Process: IDLE  ")

        self.statusbar.addPermanentWidget(VLine())
        self.statusbar.addPermanentWidget(self.statusDatabase)
        self.statusbar.addPermanentWidget(VLine())
        self.statusbar.addPermanentWidget(self.statusMining)
        self.statusbar.addPermanentWidget(VLine())
        self.statusbar.addPermanentWidget(self.statusDebugging)
        self.statusbar.addPermanentWidget(VLine())
        self.statusbar.addPermanentWidget(self.statusLabel)
        
        
        # Adding a temporary message
        self.statusbar.showMessage("UI Ready!", 1500)

    def _createToolBars(self):
        """ This method creates the UI's tool bars"""

        fileToolBar = self.addToolBar("Menu")
        fileToolBar.addAction(self.loadModelAction)
        fileToolBar.addAction(self.loadTestAction)
        fileToolBar.addAction(self.saveAction)
        fileToolBar.setMovable(False)
        fileToolBar.addSeparator()
        
        databaseToolBar = self.addToolBar("Connect DB")
        databaseToolBar.addAction(self.connectAction)
        databaseToolBar.setMovable(False)
        databaseToolBar.addSeparator()

        helpToolBar = self.addToolBar("Help")
        helpToolBar.addAction(self.githubAction)
        helpToolBar.setMovable(False)
        helpToolBar.addSeparator()

        # Using a QToolBar object and a toolbar area
        SideToolBar = QToolBar("Features", self)
        self.addToolBar(Qt.LeftToolBarArea, SideToolBar)
        SideToolBar.addAction(self.homeAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.commandAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.abductionAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.statsAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.miningAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.databaseAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.configAction)
        SideToolBar.setIconSize(QSize(50, 50))
        SideToolBar.setMovable(False)

    def _createActions(self):
        """ This method creates the UI's actions"""

        self.loadModelAction = QAction(QIcon(":load-model.svg"), "&Open Defective Program...", self)
        self.loadModelAction.setToolTip("Load Bugged Program")
        self.loadTestAction = QAction(QIcon(":load-test.svg"), "&Open Test Suite...", self)
        self.loadTestAction.setToolTip("Load Test Suite")
        self.saveAction = QAction(QIcon(":save-model.svg"), "&Save Program...", self)
        self.saveAction.setToolTip("Save Debugged Program")
        self.exitAction = QAction("&Exit", self)
        
        self.zoomDefaultAction = QAction("&Default Zoom", self)
        self.zoomInAction = QAction("Zoom &In", self)
        self.zoomOutAction = QAction("Zoom &Out", self)

        self.connectAction = QAction(QIcon(":database.svg"), "&Connect DB", self)
        self.connectAction.setToolTip("Connect to database")

        self.helpContentAction = QAction(QIcon(":help-content.svg"), "&Help Content", self)
        self.aboutAction = QAction(QIcon(":info.svg"), "&About", self)
        self.githubAction = QAction(QIcon(":github.svg"), "&Github Project...", self)
        self.githubAction.setToolTip("Go to the project page...")

        #Left SideBar Actions
        self.homeAction         =   QAction(QIcon(":home.svg")      , "Home")
        self.commandAction      =   QAction(QIcon(":command.svg")   , "Command")
        self.abductionAction    =   QAction(QIcon(":compass.svg")   , "Abduction")
        self.statsAction        =   QAction(QIcon(":bar-chart.svg") , "BarChar")
        self.miningAction       =   QAction(QIcon(":layers.svg")    , "Mining")
        self.databaseAction     =   QAction(QIcon(":database.svg")  , "Database")
        self.configAction       =   QAction(QIcon(":settings.svg")  , "Settings")
        
        self.logoutAction       =   QAction(QIcon(":log-out.svg")   , "Logout")

        self.timer = QTimer()

    def _resetLayout(self, layout = None, layout_type = QVBoxLayout):
        """ This method reset the UI's layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.deleteLayout(item.layout())
            sip.delete(layout)
        self.mainLayout = layout_type()
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.centralWidget.setLayout(self.mainLayout)
        
    def _loadConfig(self) -> Dict[str, str]:
        """ This method loads the configuration data.
        
        If the configuration file exist then the data will be loaded,
        else the dedault data will be loaded.
        :rtype: Dict[str, str]
        """
        config_file_path = Path('controller/config.yml')
        if config_file_path.exists():
            with open(config_file_path, 'r') as config_file:
                config_data = yaml.full_load(config_file)
                self._setConfigData(config_data)
        else:
            config_data = self.default_config
        return config_data

    def _readConfigData(self) -> Dict[str, str]:
        """ This method reads the configuration data from the configTable.
        
        The global variable APP_SETTINGS will be updated
        with the read configuration.
        :rtype: Dict[str, str]
        """
        config_data = {}
        rowCount = self.configTable.rowCount()
        for i in range(rowCount):
            qItemCol = self.configTable.item(i,0)
            qItemCol.setFlags(qItemCol.flags() ^ Qt.ItemIsEditable)
            key = qItemCol.text()
            value = self.configTable.item(i,1).text()
            config_data[key] = value
        DebugController.APP_SETTINGS = config_data
        return config_data

    def _setConfigData(self, config_data: Dict[str, str]) -> None:
        """ This method sets the configuration into the UI.

        All of the UI's elements will be updated given the configuration.
        """
        # Database Page
        txtHost = self.databasePage.findChild(QLineEdit, 'txtHost')
        txtHost.setText(config_data['DB_HOST'])
        txtPort = self.databasePage.findChild(QLineEdit, 'txtPort')
        txtPort.setText(config_data['DB_PORT'])
        cmbURI = self.databasePage.findChild(QComboBox, 'cmbURI')
        cmbURI.setCurrentText(config_data['DB_URI'])
        txtDatabase = self.databasePage.findChild(QLineEdit, 'txtDatabase')
        txtDatabase.setText(config_data['DEBUG_DB_NAME'])
        txtCollection = self.databasePage.findChild(QLineEdit, 'txtCollection')
        txtCollection.setText(config_data['DEBUG_DB_PATTERNS_COLLECTION'])
        # Debugging Page
        snbTimeout = self.AbductionPage.findChild(QDoubleSpinBox, 'snbTimeout')
        snbTimeout.setValue(float(config_data['MAXIMUM_TEST_TIMEOUT']))
        # Mining Page
        txtReposDatabase = self.miningPage.findChild(QLineEdit, 'txtReposDatabase')
        txtReposDatabase.setText(config_data['MINING_DB_NAME'])
        txtPatternsCollection = self.miningPage.findChild(QLineEdit, 'txtPatternsCollection')
        txtPatternsCollection.setText(config_data['MINING_DB_PATTERNS_COLLECTION'])
        txtReposCollection = self.miningPage.findChild(QLineEdit, 'txtReposCollection')
        txtReposCollection.setText(config_data['MINING_DB_REPO_COLLECTION'])
        # Setting Page
        for i, (key, value) in enumerate(config_data.items()):
            qItemCol = QTableWidgetItem(key)
            qItemCol.setFlags(qItemCol.flags() ^ Qt.ItemIsEditable)
            self.configTable.setItem(i, 0, qItemCol)
            self.configTable.setItem(i, 1, QTableWidgetItem(value))
        self.configTable.sortItems(0, Qt.AscendingOrder)
        self._readConfigData

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AbinView()
    win.show()
    sys.exit(app.exec_())
