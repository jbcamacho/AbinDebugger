"""
This module is the view of the system.
This is the view representation of the MVC software pattern.
"""
import sys
import resources.qrc_resources as qrc_resources
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5 import sip, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, 
    QToolBar, QAction, QVBoxLayout, QFrame,
    QStackedWidget, QWidget, QTableWidget
)
from controller.DebugController import ConnectionStatus

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
        self.resize(1000, 800)
        
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
        self.allPages.findChild(QTableWidget, 'tableTestSuite').horizontalHeader().setVisible(True)
        self.allPages.findChild(QTableWidget, 'tableTypes').horizontalHeader().setVisible(True)
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        self._createStatusBar()        
    
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
        SideToolBar.addAction(self.barChartAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.miningAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.databaseAction)
        SideToolBar.addSeparator()
        SideToolBar.addAction(self.settingsAction)
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
        self.barChartAction     =   QAction(QIcon(":bar-chart.svg") , "BarChar")
        self.miningAction       =   QAction(QIcon(":layers.svg")    , "Mining")
        self.databaseAction     =   QAction(QIcon(":database.svg")  , "Database")
        self.settingsAction     =   QAction(QIcon(":settings.svg")  , "Settings")
        
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
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AbinView()
    win.show()
    sys.exit(app.exec_())
