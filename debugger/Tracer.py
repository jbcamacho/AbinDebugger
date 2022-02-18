import sys
from types import FrameType, TracebackType
from typing import Any, Callable, Optional, Type, TextIO

from debugger.StackInspector import StackInspector

class Tracer(StackInspector):
    """A class for tracing a piece of code. Use as `with Tracer(): block()`"""

    def __init__(self, *, file: TextIO = sys.stdout) -> None:
        """Trace a block of code, sending logs to `file` (default: stdout)"""
        self.original_trace_function: Optional[Callable] = None
        self.file = file

    def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        """Tracing function. To be overridden in subclasses."""
        self.log(event, frame.f_lineno, frame.f_code.co_name, frame.f_locals)

    def _traceit(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        """Internal tracing function."""
        if self.our_frame(frame):
            # Do not trace our own methods
            pass
        else:
            self.traceit(frame, event, arg)
        return self._traceit

    def log(self, *objects: Any, 
            sep: str = ' ', end: str = '\n', 
            flush: bool = True) -> None:
        """
        Like `print()`, but always sending to `file` given at initialization,
        and flushing by default.
        """
        print(*objects, sep=sep, end=end, file=self.file, flush=flush)

    def __enter__(self) -> Any:
        """Called at begin of `with` block. Turn tracing on."""
        self.original_trace_function = sys.gettrace()
        sys.settrace(self._traceit)

        # This extra line also enables tracing for the current block
        # inspect.currentframe().f_back.f_trace = self._traceit
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException, 
                 exc_traceback: TracebackType) -> Optional[bool]:
        """
        Called at end of `with` block. Turn tracing off.
        Return `None` if ok, not `None` if internal error.
        """
        sys.settrace(self.original_trace_function)

        # Note: we must return a non-True value here,
        # such that we re-raise all exceptions
        if self.is_internal_error(exc_tp, exc_value, exc_traceback):
            return False  # internal error
        else:
            return None  # all ok