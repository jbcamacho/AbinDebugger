from model.debugger.Collector import CoverageCollector
from types import FrameType
from typing import Any
import controller.DebugController as DebugController

class AbinCollector(CoverageCollector):
    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        """
        Save coverage for an observed event.
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