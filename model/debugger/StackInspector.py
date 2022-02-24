"""
This module is used to inspect a call stack in order to track
a function location, source code and/or definitions.

The content of this file can be found in The Debugging Book.
Andreas Zeller: "The Debugging Book". Retrieved 2022-02-02 19:00:00-06:00.
@book{debuggingbook2021,
    author = {Andreas Zeller},
    title = {The Debugging Book},
    year = {2021},
    publisher = {CISPA Helmholtz Center for Information Security},
    howpublished = {\url{https://www.debuggingbook.org/}},
    note = {Retrieved 2022-02-02 19:00:00-06:00},
    url = {https://www.debuggingbook.org/},
    urldate = {2021-10-13 13:24:19+02:00}
}
"""
import inspect
import warnings
import traceback

from types import FunctionType, FrameType, TracebackType
from typing import Any, Dict, Tuple, Callable, Optional, Type, cast

Location = Tuple[Callable, int]

class StackInspector():
    """Provide functions to inspect the stack"""

    def caller_frame(self) -> FrameType:
        """Return the frame of the caller."""

        # Walk up the call tree until we leave the current class
        frame = cast(FrameType, inspect.currentframe())

        while self.our_frame(frame):
            frame = cast(FrameType, frame.f_back)

        return frame

    def our_frame(self, frame: FrameType) -> bool:
        """Return true if `frame` is in the current (inspecting) class."""
        return isinstance(frame.f_locals.get('self'), self.__class__)
    
    def caller_globals(self) -> Dict[str, Any]:
        """Return the globals() environment of the caller."""
        return self.caller_frame().f_globals

    def caller_locals(self) -> Dict[str, Any]:
        """Return the locals() environment of the caller."""
        return self.caller_frame().f_locals

    def caller_location(self) -> Location:
        """Return the location (func, lineno) of the caller."""
        return self.caller_function(), self.caller_frame().f_lineno

    def search_frame(self, name: str, frame: Optional[FrameType] = None) -> \
        Tuple[Optional[FrameType], Optional[Callable]]:
        """
        Return a pair (`frame`, `item`) 
        in which the function `name` is defined as `item`.
        """
        if frame is None:
            frame = self.caller_frame()

        while frame:
            item = None
            if name in frame.f_globals:
                item = frame.f_globals[name]
            if name in frame.f_locals:
                item = frame.f_locals[name]
            if item and callable(item):
                return frame, item

            frame = cast(FrameType, frame.f_back)

        return None, None

    def search_func(self, name: str, frame: Optional[FrameType] = None) -> \
        Optional[Callable]:
        """Search in callers for a definition of the function `name`"""
        frame, func = self.search_frame(name, frame)
        return func

    # Avoid generating functions more than once
    _generated_function_cache: Dict[Tuple[str, int], Callable] = {}

    def create_function(self, frame: FrameType) -> Callable:
        """Create function for given frame"""
        name = frame.f_code.co_name
        cache_key = (name, frame.f_lineno)
        if cache_key in self._generated_function_cache:
            return self._generated_function_cache[cache_key]

        try:
            # Create new function from given code
            generated_function = cast(Callable,
                                      FunctionType(frame.f_code,
                                                   globals=frame.f_globals,
                                                   name=name))
        except TypeError:
            # Unsuitable code for creating a function
            # Last resort: Return some function
            generated_function = self.unknown

        except Exception as exc:
            # Any other exception
            warnings.warn(f"Couldn't create function for {name} "
                          f" ({type(exc).__name__}: {exc})")
            generated_function = self.unknown

        self._generated_function_cache[cache_key] = generated_function
        return generated_function
    
    def caller_function(self) -> Callable:
        """Return the calling function"""
        frame = self.caller_frame()
        name = frame.f_code.co_name
        func = self.search_func(name)
        if func:
            return func

        if not name.startswith('<'):
            warnings.warn(f"Couldn't find {name} in caller")

        return self.create_function(frame)

    def unknown(self) -> None:  # Placeholder for unknown functions
        pass

    def is_internal_error(self, exc_tp: Type, 
                          exc_value: BaseException, 
                          exc_traceback: TracebackType) -> bool:
        """Return True if exception was raised from `StackInspector` or a subclass."""
        if not exc_tp:
            return False

        for frame, lineno in traceback.walk_tb(exc_traceback):
            if self.our_frame(frame):
                return True

        return False