import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QFrame, QVBoxLayout,
    QPlainTextEdit, QSpinBox, QPushButton, QLineEdit
)

class AbductionPageView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.lblModel = QLabel(self)
        self.lblModel.setAlignment(Qt.AlignCenter)
        self.lblModel.setText('Current Model')
        self.layout.addWidget(self.lblModel, 6, 3, 1, 1, Qt.AlignTop)
        self.lblComplexity = QLabel(self)
        self.lblComplexity.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lblComplexity.setText('Complexity')
        self.layout.addWidget(self.lblComplexity, 7, 2, 1, 1)
        self.lblFunctionName = QLabel(self)
        self.lblFunctionName.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lblFunctionName.setText('Function Name')
        self.layout.addWidget(self.lblFunctionName, 8, 2, 1, 1)
        self.lblAbductionChart = QLabel(self)
        self.lblAbductionChart.setAlignment(Qt.AlignCenter)
        self.lblAbductionChart.setText('Abduction Complexity Chart')
        self.layout.addWidget(self.lblAbductionChart, 4, 3, 1, 1, Qt.AlignTop)
        self.lblLogging = QLabel(self)
        self.lblLogging.setAlignment(Qt.AlignCenter)
        self.lblLogging.setText("Logging Info")
        self.layout.addWidget(self.lblLogging, 9, 1, 1, 1, Qt.AlignTop)
        
        self.txtModel = QPlainTextEdit(self)
        self.layout.addWidget(self.txtModel, 5, 3, 1, 1, Qt.AlignVCenter)
        self.txtLogging = QPlainTextEdit(self)
        self.layout.addWidget(self.txtLogging, 0, 1, 8, 1, Qt.AlignHCenter)
        self.txtFunctionName = QLineEdit(self)
        self.layout.addWidget(self.txtFunctionName, 8, 3, 1, 1)


        self.snbComplexity = QSpinBox(self)
        self.snbComplexity.setAlignment(Qt.AlignCenter)
        self.snbComplexity.setValue(2)
        self.layout.addWidget(self.snbComplexity, 7, 3, 1, 1)
        self.btnStartDebug = QPushButton(self)
        self.btnStartDebug.setText('Start Debugging')
        self.layout.addWidget(self.btnStartDebug, 9, 3, 1, 1)


        self.frmAbductionChart = QFrame(self)
        self.frmAbductionChart.setFrameShape(QFrame.StyledPanel)
        self.frmAbductionChart.setFrameShadow(QFrame.Raised)
        self.frmChartLayout = QVBoxLayout(self.frmAbductionChart)
        self.layout.addWidget(self.frmAbductionChart, 0, 3, 4, 1)

        self.vLineLogging = QFrame(self)
        self.vLineLogging.setFrameShape(QFrame.VLine)
        self.vLineLogging.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.vLineLogging, 0, 2, 7, 1, Qt.AlignHCenter)

        self.hLineLogging = QFrame(self)
        self.hLineLogging.setFrameShape(QFrame.HLine)
        self.hLineLogging.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.hLineLogging, 10, 1, 1, 1)