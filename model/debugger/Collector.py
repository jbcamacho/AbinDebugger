from model.debugger.Tracer import Tracer
from model.debugger.StackInspector import StackInspector
from types import FrameType, TracebackType
from typing import Any, Set, Dict, Tuple, Callable, Optional, Type, List, Union

Coverage = Set[Tuple[Callable, int]]

class Collector(Tracer):
    def __init__(self) -> None:
        """Constructor."""
        self._function: Optional[Callable] = None
        self._args: Optional[Dict[str, Any]] = None
        self._argstring: Optional[str] = None
        self._exception: Optional[Type] = None
        self.items_to_ignore: List[Union[Type, Callable]] = [self.__class__]

    def traceit(self, frame: FrameType, event: str, arg: Any) -> None:
        """
        Tracing function.
        Saves the first function and calls collect().
        """
        for item in self.items_to_ignore:
            if (isinstance(item, type) and 'self' in frame.f_locals and
                isinstance(frame.f_locals['self'], item)):
                # Ignore this class
                return
            if item.__name__ == frame.f_code.co_name:
                # Ignore this function
                return

        if self._function is None and event == 'call':
            # Save function
            self._function = self.create_function(frame)
            self._args = frame.f_locals.copy()
            self._argstring = ", ".join([f"{var}={repr(self._args[var])}" 
                                         for var in self._args])

        self.collect(frame, event, arg)

    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        """Collector function. To be overloaded in subclasses."""
        pass

    def events(self) -> Set:
        """Return a collection of events. To be overridden in subclasses."""
        return set()

    def id(self) -> str:
        """Return an identifier for the collector, 
        created from the first call"""
        return f"{self.function().__name__}({self.argstring()})"

    def function(self) -> Callable:
        """Return the function from the first call, as a function object"""
        if not self._function:
            raise ValueError("No call collected")
        return self._function

    def argstring(self) -> str:
        """
        Return the list of arguments from the first call,
        as a printable string
        """
        if not self._argstring:
            raise ValueError("No call collected")
        return self._argstring

    def args(self) -> Dict[str, Any]:
        """Return a dict of argument names and values from the first call"""
        if not self._args:
            raise ValueError("No call collected")
        return self._args

    def exception(self) -> Optional[Type]:
        """Return the exception class from the first call,
        or None if no exception was raised."""
        return self._exception

    def __repr__(self) -> str:
        """Return a string representation of the collector"""
        # We use the ID as default representation when printed
        return self.id()

    def covered_functions(self) -> Set[Callable]:
        """Set of covered functions. To be overloaded in subclasses."""
        return set()

    def coverage(self) -> Coverage:
        """
        Return a set (function, lineno) with locations covered.
        To be overloaded in subclasses.
        """
        return set()

    def add_items_to_ignore(self,
                            items_to_ignore: List[Union[Type, Callable]]) \
                            -> None:
        """
        Define additional classes and functions to ignore during collection
        (typically `Debugger` classes using these collectors).
        """
        self.items_to_ignore += items_to_ignore

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        """Exit the `with` block."""
        ret = super().__exit__(exc_tp, exc_value, exc_traceback)

        if not self._function:
            if exc_tp:
                return False  # re-raise exception
            else:
                raise ValueError("No call collected")

        return ret

class CoverageCollector(Collector, StackInspector):
    """A class to record covered locations during execution."""

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()
        self._coverage: Coverage = set()

    def collect(self, frame: FrameType, event: str, arg: Any) -> None:
        """
        Save coverage for an observed event.
        """
        name = frame.f_code.co_name
        function = self.search_func(name, frame)

        if function is None:
            function = self.create_function(frame)

        location = (function, frame.f_lineno)
        self._coverage.add(location)

    def events(self) -> Set[Tuple[str, int]]:
        """
        Return the set of locations covered.
        Each location comes as a pair (`function_name`, `lineno`).
        """
        return {(func.__name__, lineno) for func, lineno in self._coverage}

    def covered_functions(self) -> Set[Callable]:
        """Return a set with all functions covered."""
        return {func for func, lineno in self._coverage}

    def coverage(self) -> Coverage:
        """Return a set (function, lineno) with all locations covered."""
        return self._coverage