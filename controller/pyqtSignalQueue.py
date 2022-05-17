"""
This module implements a Queue handler for the threading
using the pyqtSignal class.
"""
from PyQt5.QtCore import QObject, pyqtSignal


class pyqtSignalQueueHandler(QObject):
    sigEnqueue: pyqtSignal = pyqtSignal()
    def __init__(self) -> None:
        QObject.__init__(self)
        self.x_data = []
        self.y_data = []

    def enqueue(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)
        # self.sigEnqueue.emit()

    def dequeue_all(self):
        self.x_data = []
        self.y_data = []
    
    def is_empty(self):
        return self.x_data and self.y_data