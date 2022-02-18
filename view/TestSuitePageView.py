
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QTableWidget, QComboBox, QWidget, QGridLayout, QHeaderView
)

class TestSuitePageView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.tableTypes = self._createTypesTable()
        self.layout.addWidget(self.tableTypes, 0, 0)

        self.tableTestSuite = self._createTestSuiteTable()
        self.layout.addWidget(self.tableTestSuite, 0, 1)

    def _createTestSuiteTable(self):
        table = QTableWidget(self)
        table.setRowCount(2)
        table.setColumnCount(3)
        table.setFixedHeight(400)
        table.setHorizontalHeaderLabels(['test_case', 'expected_output', 'input_args'])
        table.resizeColumnsToContents()
        return table

    def _createTypesTable(self):
        table = QTableWidget(self)
        table.setRowCount(2)
        table.setColumnCount(2)
        table.setFixedSize(200, 400)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setHorizontalHeaderLabels(['input_args', 'type'])
        #combo = comboTypes(self)
        #table.setCellWidget(1, 1, combo)
        table.resizeColumnsToContents()
        return table


class comboTypes(QComboBox):
    def __init__(self, parent = None):
        super().__init__(parent)
        #self.setStyleSheet('font-size: 25px')
        self.addItems(['Str', 'Int', 'Float', 'List', 'Dict', 'Tuple'])
        self.currentIndexChanged.connect(self.getComboValue)

    def getComboValue(self):
        print(self.currentText())
        # return self.currentText()