
from debugger.Collector import Collector, CoverageCollector
import inspect
from types import TracebackType
from typing import Any, Set, Dict, Callable, Optional, Tuple, Type, List, Union
import math
from cgitb import html


class StatisticalDebugger():
    """A class to collect events for multiple outcomes."""

    def __init__(self, collector_class: Type = CoverageCollector, log: bool = False):
        """Constructor. Use instances of `collector_class` to collect events."""
        self.collector_class = collector_class
        self.collectors: Dict[str, List[Collector]] = {}
        self.log = log

    def collect(self, outcome: str, *args: Any, **kwargs: Any) -> Collector:
        """Return a collector for the given outcome. 
        Additional args are passed to the collector."""
        collector = self.collector_class(*args, **kwargs)
        collector.add_items_to_ignore([self.__class__])
        return self.add_collector(outcome, collector)

    def add_collector(self, outcome: str, collector: Collector) -> Collector:
        if outcome not in self.collectors:
            self.collectors[outcome] = []
        self.collectors[outcome].append(collector)
        return collector

    def all_events(self, outcome: Optional[str] = None) -> Set[Any]:
        """Return a set of all events observed."""
        all_events = set()

        if outcome:
            if outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    all_events.update(collector.events())
        else:
            for outcome in self.collectors:
                for collector in self.collectors[outcome]:
                    all_events.update(collector.events())

        return all_events




class DifferenceDebugger(StatisticalDebugger):
    """A class to collect events for passing and failing outcomes."""

    PASS = 'PASS'
    FAIL = 'FAIL'

    def collect_pass(self, *args: Any, **kwargs: Any) -> Collector:
        """Return a collector for passing runs."""
        return self.collect(self.PASS, *args, **kwargs)

    def collect_fail(self, *args: Any, **kwargs: Any) -> Collector:
        """Return a collector for failing runs."""
        return self.collect(self.FAIL, *args, **kwargs)

    def pass_collectors(self) -> List[Collector]:
        return self.collectors[self.PASS]

    def fail_collectors(self) -> List[Collector]:
        return self.collectors[self.FAIL]

    def all_fail_events(self) -> Set[Any]:
        """Return all events observed in failing runs."""
        return self.all_events(self.FAIL)

    def all_pass_events(self) -> Set[Any]:
        """Return all events observed in passing runs."""
        return self.all_events(self.PASS)

    def only_fail_events(self) -> Set[Any]:
        """Return all events observed only in failing runs."""
        return self.all_fail_events() - self.all_pass_events()

    def only_pass_events(self) -> Set[Any]:
        """Return all events observed only in passing runs."""
        return self.all_pass_events() - self.all_fail_events()

    
    def __enter__(self) -> Any:
        """Enter a `with` block. Collect coverage and outcome;
        classify as FAIL if the block raises an exception,
        and PASS if it does not.
        """
        self.collector = self.collector_class()
        self.collector.add_items_to_ignore([self.__class__])
        self.collector.__enter__()
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        """Exit the `with` block."""
        status = self.collector.__exit__(exc_tp, exc_value, exc_traceback)

        if status is None:
            pass
        else:
            return False  # Internal error; re-raise exception

        if exc_tp is None:
            outcome = self.PASS
        else:
            outcome = self.FAIL

        self.add_collector(outcome, self.collector)
        return True  # Ignore exception, if any





class SpectrumDebugger(DifferenceDebugger):
    def suspiciousness(self, event: Any) -> Optional[float]:
        """
        Return a suspiciousness value in the range [0, 1.0]
        for the given event, or `None` if unknown.
        To be overloaded in subclasses.
        """
        return None

    def tooltip(self, event: Any) -> str:
        """
        Return a tooltip for the given event (default: percentage).
        To be overloaded in subclasses.
        """
        return self.percentage(event)

    def percentage(self, event: Any) -> str:
        """
        Return the suspiciousness for the given event as percentage string.
        """
        suspiciousness = self.suspiciousness(event)
        if suspiciousness is not None:
            return str(int(suspiciousness * 100)).rjust(3) + '%'
        else:
            return ' ' * len('100%')

    def code(self, functions: Optional[Set[Callable]] = None, *, 
             color: bool = False, suspiciousness: bool = False,
             line_numbers: bool = True) -> str:
        """
        Return a listing of `functions` (default: covered functions).
        If `color` is True, render as HTML, using suspiciousness colors.
        If `suspiciousness` is True, include suspiciousness values.
        If `line_numbers` is True (default), include line numbers.
        """

        if not functions:
            functions = self.covered_functions()

        out = ""
        seen = set()
        for function in functions:
            source_lines, starting_line_number = \
               inspect.getsourcelines(function)

            if (function.__name__, starting_line_number) in seen:
                continue
            seen.add((function.__name__, starting_line_number))

            if out:
                out += '\n'
                if color:
                    out += '<p/>'

            line_number = starting_line_number
            for line in source_lines:
                if color:
                    line = html.escape(line)
                    if line.strip() == '':
                        line = '&nbsp;'

                location = (function.__name__, line_number)
                location_suspiciousness = self.suspiciousness(location)
                if location_suspiciousness is not None:
                    tooltip = f"Line {line_number}: {self.tooltip(location)}"
                else:
                    tooltip = f"Line {line_number}: not executed"

                if suspiciousness:
                    line = self.percentage(location) + ' ' + line

                if line_numbers:
                    line = str(line_number).rjust(4) + ' ' + line

                line_color = self.color(location)

                if color and line_color:
                    line = f'''<pre style="background-color:{line_color}"
                    title="{tooltip}">{line.rstrip()}</pre>'''
                elif color:
                    line = f'<pre title="{tooltip}">{line}</pre>'
                else:
                    line = line.rstrip()

                out += line + '\n'
                line_number += 1

        return out

    def _repr_html_(self) -> str:
        """When output in Jupyter, visualize as HTML"""
        return self.code(color=True)

    def __str__(self) -> str:
        """Show code as string"""
        return self.code(color=False, suspiciousness=True)

    def __repr__(self) -> str:
        """Show code as string"""
        return self.code(color=False, suspiciousness=True)




class DiscreteSpectrumDebugger(SpectrumDebugger):
    """Visualize differences between executions using three discrete colors"""

    def suspiciousness(self, event: Any) -> Optional[float]:
        """
        Return a suspiciousness value [0, 1.0]
        for the given event, or `None` if unknown.
        """
        passing = self.all_pass_events()
        failing = self.all_fail_events()

        if event in passing and event in failing:
            return 0.5
        elif event in failing:
            return 1.0
        elif event in passing:
            return 0.0
        else:
            return None

    def color(self, event: Any) -> Optional[str]:
        """
        Return a HTML color for the given event.
        """
        suspiciousness = self.suspiciousness(event)
        if suspiciousness is None:
            return None

        if suspiciousness > 0.8:
            return 'mistyrose'
        if suspiciousness >= 0.5:
            return 'lightyellow'

        return 'honeydew'

    def tooltip(self, event: Any) -> str:
        """Return a tooltip for the given event."""
        passing = self.all_pass_events()
        failing = self.all_fail_events()

        if event in passing and event in failing:
            return "in passing and failing runs"
        elif event in failing:
            return "only in failing runs"
        elif event in passing:
            return "only in passing runs"
        else:
            return "never"




class ContinuousSpectrumDebugger(DiscreteSpectrumDebugger):
    """Visualize differences between executions using a color spectrum"""

    def collectors_with_event(self, event: Any, category: str) -> Set[Collector]:
        """
        Return all collectors in a category
        that observed the given event.
        """
        #all_runs = self.collectors[category]
        all_runs = self.collectors.get(category, {})
        collectors_with_event = set(collector for collector in all_runs 
                                    if event in collector.events())
        return collectors_with_event

    def collectors_without_event(self, event: Any, category: str) -> Set[Collector]:
        """
        Return all collectors in a category
        that did not observe the given event.
        """
        #all_runs = self.collectors[category]
        all_runs = self.collectors.get(category, {})
        collectors_without_event = set(collector for collector in all_runs 
                              if event not in collector.events())
        return collectors_without_event

    def event_fraction(self, event: Any, category: str) -> float:
        if category not in self.collectors:
            return 0.0

        all_collectors = self.collectors[category]
        collectors_with_event = self.collectors_with_event(event, category)
        fraction = len(collectors_with_event) / len(all_collectors)
        # print(f"%{category}({event}) = {fraction}")
        return fraction

    def passed_fraction(self, event: Any) -> float:
        return self.event_fraction(event, self.PASS)

    def failed_fraction(self, event: Any) -> float:
        return self.event_fraction(event, self.FAIL)

    def hue(self, event: Any) -> Optional[float]:
        """Return a color hue from 0.0 (red) to 1.0 (green)."""
        passed = self.passed_fraction(event)
        failed = self.failed_fraction(event)
        if passed + failed > 0:
            return passed / (passed + failed)
        else:
            return None
    
    def suspiciousness(self, event: Any) -> Optional[float]:
        hue = self.hue(event)
        if hue is None:
            return None
        return 1 - hue

    def tooltip(self, event: Any) -> str:
        return self.percentage(event)

    def brightness(self, event: Any) -> float:
        return max(self.passed_fraction(event), self.failed_fraction(event))

    def color(self, event: Any) -> Optional[str]:
        hue = self.hue(event)
        if hue is None:
            return None
        saturation = self.brightness(event)

        # HSL color values are specified with: 
        # hsl(hue, saturation, lightness).
        return f"hsl({hue * 120}, {saturation * 100}%, 80%)"



class RankingDebugger(DiscreteSpectrumDebugger):
    """Rank events by their suspiciousness"""

    def rank(self) -> List[Any]:
        """Return a list of events, sorted by suspiciousness, highest first."""

        def susp(event: Any) -> float:
            suspiciousness = self.suspiciousness(event)
            assert suspiciousness is not None
            return suspiciousness

        events = list(self.all_events())
        events.sort(key=susp, reverse=True)
        return events

    def __repr__(self) -> str:
        return repr(self.rank())


class TarantulaDebugger(ContinuousSpectrumDebugger, RankingDebugger):
    """Spectrum-based Debugger using the Tarantula metric for suspiciousness"""
    pass

class OchiaiDebugger(ContinuousSpectrumDebugger, RankingDebugger):
    """Spectrum-based Debugger using the Ochiai metric for suspiciousness"""

    def suspiciousness(self, event: Any) -> Optional[float]:
        failed = len(self.collectors_with_event(event, self.FAIL))
        not_in_failed = len(self.collectors_without_event(event, self.FAIL))
        passed = len(self.collectors_with_event(event, self.PASS))

        try:
            return failed / math.sqrt((failed + not_in_failed) * (failed + passed))
        except ZeroDivisionError:
            return None

    def hue(self, event: Any) -> Optional[float]:
        suspiciousness = self.suspiciousness(event)
        if suspiciousness is None:
            return None
        return 1 - suspiciousness


class StatisticalRankingDebugger(RankingDebugger):
    pass


from enum import Enum
ranking_lst = ['Assign', 'Expr', 'If', 'Return', 'FunctionDef',
'ImportFrom', 'Raise', 'Assert', 'ExceptHandler', 'For', 'AugAssign',
'With', 'ClassDef', 'Import', 'Call', 'AnnAssign', 'While', 'AsyncFunctionDef',
'Pass', 'Delete', 'arg', 'Subscript', 'Name', 'Break', 'Attribute', 'Global',
'Try', 'NameConstant', 'AsyncFor']

#StatisticalRanking = Enum('StatisticalRanking', ranking_lst)
InfluencePath = List[Tuple[str, int]]

class AbductiveDebugger(OchiaiDebugger):
    StatisticalRanking: Dict[str, int] = {
        'Assign':1,
        'Expr':2,
        'If':3,
        'Return':4,
        'FunctionDef':5,
        'ImportFrom':6,
        'Raise':7,
        'Assert':8,
        'ExceptHandler':9,
        'For':10,
        'AugAssign':11,
        'With':12,
        'ClassDef':13,
        'Import':14,
        'Call':15,
        'AnnAssign':16,
        'While':17,
        'AsyncFunctionDef':18,
        'Pass':19,
        'Delete':20,
        'arg':21,
        'Subscript':22,
        'Name':23,
        'Break':24,
        'Attribute':25,
        'Global':26,
        'Try':27,
        'NameConstant':28,
        'AsyncFor':29
    }
    
    def __init__(self, collector_class: Type = CoverageCollector, log: bool = False):
        super().__init__(collector_class, log)
        self.influence_path: List = []

    def get_influence_path(self) -> InfluencePath:
        """Return a list of events, sorted by suspiciousness, highest first."""
        self.influence_path = list(filter(lambda x: x[0] not in ['debug', 'isEnabledFor'], self.rank()))
        #top_candidate = self.bug_candidates.pop(0)

        return self.influence_path
    
    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        try:
            return super().__repr__()
        except Exception as e:
            return f"GOOD: {e}"


Debugger = Union[AbductiveDebugger, OchiaiDebugger, TarantulaDebugger, RankingDebugger, ContinuousSpectrumDebugger, DiscreteSpectrumDebugger, SpectrumDebugger, DifferenceDebugger, StatisticalDebugger]


