import sys
import resources.qrc_resources as qrc_resources
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5 import sip, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, QToolBar, QAction, QVBoxLayout, QFrame,
    QStackedWidget, QWidget, QTableWidget
)
from view.TestSuitePageView import TestSuitePageView
from view.AbductionView import AbductionPageView

class AbinDebuggerPages(QStackedWidget):
    def __init__(self, parent = None):
        QStackedWidget.__init__(self, parent)
        uic.loadUi('view/AbinDebuggerPages.ui', self)

class AbinView(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
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
        self.csvTestSuite = None

        
    
    def _createMenuBar(self):
        menuBar = self.menuBar()
        
        #fileMenu = menuBar.addMenu(QIcon(":menu.svg"), "&Menu")
        fileMenu = menuBar.addMenu("&Menu")
        fileMenu.addAction(self.loadModelAction)
        fileMenu.addAction(self.loadTestAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        # editMenu = menuBar.addMenu("&Edit")
        # editMenu.addAction(self.copyAction)
        # editMenu.addAction(self.pasteAction)
        # editMenu.addAction(self.cutAction)
        # editMenu.addSeparator()

        # findMenu = editMenu.addMenu("Find and Replace")
        # findMenu.addAction("Find...")
        # findMenu.addAction("Replace...")

        helpMenu = menuBar.addMenu("&Help") #QIcon(":help-content.svg")
        helpMenu.addAction(self.helpContentAction)
        helpMenu.addAction(self.aboutAction)

    def _createStatusBar(self):
        self.statusbar = self.statusBar()
        # Adding a temporary message
        self.statusbar.showMessage("Ready", 3000)
        self.statusLabel = QLabel()
        self.statusLabel.setText(f"Home")
        self.statusbar.addPermanentWidget(self.statusLabel)

    def _createToolBars(self):
        # 
        fileToolBar = self.addToolBar("Menu")
        fileToolBar.addAction(self.loadModelAction)
        fileToolBar.addAction(self.loadTestAction)
        fileToolBar.addAction(self.saveAction)
        fileToolBar.setMovable(False)

        # editToolBar = self.addToolBar("Edit")
        # editToolBar.addAction(self.copyAction)
        # editToolBar.addAction(self.pasteAction)
        # editToolBar.addAction(self.cutAction)
        # editToolBar.setMovable(False)

        # Using a QToolBar object and a toolbar area
        SideToolBar = QToolBar("Help", self)
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
        # Creating actions using the second constructor
        self.loadModelAction = QAction(QIcon(":load-model.svg"), "&Open Defective Program...", self)
        self.loadModelAction.setToolTip("Load Bugged Program")
        self.loadTestAction = QAction(QIcon(":load-test.svg"), "&Open Test Suite...", self)
        self.loadTestAction.setToolTip("Load Test Suite")
        self.saveAction = QAction(QIcon(":save-model.svg"), "&Save Program...", self)
        self.saveAction.setToolTip("Save Debugged Program")
        self.exitAction = QAction("&Exit", self)
        # self.copyAction = QAction(QIcon(":edit-copy.svg"), "&Copy", self)
        # self.pasteAction = QAction(QIcon(":edit-paste.svg"), "&Paste", self)
        # self.cutAction = QAction(QIcon(":edit-cut.svg"), "C&ut", self)
        self.helpContentAction = QAction(QIcon(":help-content.svg"), "&Help Content", self)
        self.aboutAction = QAction(QIcon(":info.svg"), "&About", self)

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
        
    def _addTestSuitePage(self):
        return TestSuitePageView()

    def _addAbductionPage(self):
        return AbductionPageView()

    def _addDatabasePage(self):
        pass

    def _addCommandPage(self):
        pass

    def _addHomePage(self):
        pass

    def _addMiningPage(self):
        pass

    def _addStatsPage(self):
        pass

    def _addSettingsPage(self):
        pass  
        



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AbinView()
    win.show()
    sys.exit(app.exec_())
