"""
This module is used to collect the events present in a trace of execution.
The execution is carried out by a thread; a control variable
(i. e. TIMEOUT_SIGNAL_RECEIVED) is necesary to raise a timeout exception.
"""
from model.debugger.Collector import CoverageCollector
from types import FrameType
from typing import Any
import controller.DebugController as DebugController

class AbinCollector(CoverageCollector):
    """ This class is implemented upon the CoverageCollector class. """
    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        """
        Save coverage for an observed event.

        In case a timeout is triggered by signal.SIGALRM,
        the event will be detected by the change in the value
        of the control variable TIMEOUT_SIGNAL_RECEIVED.
        If the value is equal to 1 the function will raise a timeout exception.

        :param frame: ...
        :type  frame: FrameType
        :param event: ...
        :type  event: str
        :param arg: ...
        :type  arg: Any
        :rtype: None
        """
        if DebugController.TIMEOUT_SIGNAL_RECEIVED == 1:
            DebugController.TIMEOUT_SIGNAL_RECEIVED = 2
            raise TimeoutError('DEBUG_SINAL_RECEIVED')
        name = frame.f_code.co_name
        function = self.search_func(name, frame)

        if function is None:
            function = self.create_function(frame)

        location = (function, frame.f_lineno)
        self._coverage.add(location)