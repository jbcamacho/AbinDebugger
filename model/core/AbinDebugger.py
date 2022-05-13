"""
This module is used to correlate the collected events present
in a trace of execution in order to determinate/suggest which statement
of the bugged program holds the defect.
The statements are ordered by the Ochiai metric and the statistical ranking
provided by the bug patterns in the database.
"""
from model.debugger.AbinCollector import AbinCollector
from model.debugger.StatisticalDebugger import OchiaiDebugger
from typing import Union, Tuple, Type, List, Dict, Optional
from types import TracebackType, ModuleType
from model.abstractor.NodeMapper import ASTNode
from model.abstractor.Visitors import TargetVisitor, CallVisitor, FunctionVisitor, StatementVisitor
import controller.DebugController as DebugController

InfluencePath = List[Tuple[str, int]]

class AbinDebugger(OchiaiDebugger):
    """ This class is implemented upon the OchiaiDebugger class. """
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
    influence_path: InfluencePath
    susp_threshold: int
    def __init__(self, susp_threshold: int = 0, collector_class: Type = AbinCollector, log: bool = False) -> None:
        """Constructor Method"""
        super().__init__(collector_class, log)
        self.influence_path: List = []
        if susp_threshold:
            self.susp_threshold = susp_threshold
        else:
            self.susp_threshold = float(DebugController.APP_SETTINGS['SUSPICIOUSNESS_THRESHOLD'])
            

    def get_influence_path(self, model: ModuleType, target_func: str) -> InfluencePath:
        """Return a list of failure candidates.
        
        The list is sorted by suspiciousness (Ochiai Metric)
        and statistical ranking.

        :param model: The module that holds the bugged program.
        :type  model: ModuleType
        :param target_func: The function that triggers the bugged program.
        :type  target_func: str
        :rtype: InfluencePath
        """
        if model is None: return []
        
        func_names = self.get_all_func_names(model)
        ranked_events = list(filter(lambda x: x[0] in func_names, self.rank()))
        first_ranked_lineno = ranked_events[0][1]

        ranked_events_susp = list(map(lambda x: (x + (self.suspiciousness(x),)), ranked_events))
        ranked_events_filtered = self.susp_threshold_filter(ranked_events_susp)
        #print(ranked_events_susp)
        unique_suspiciousness_values = set(map(lambda x:x[2], ranked_events_filtered))
        unique_suspiciousness_sorted = sorted(unique_suspiciousness_values, reverse=True)
        group_by_suspiciousness = [[y[:2] for y in ranked_events_filtered if y[2]==x] for x in unique_suspiciousness_sorted]

        new_path = []
        for elem in group_by_suspiciousness:
            sorted_group = sorted(elem, key=lambda i: abs(first_ranked_lineno - i[1]))
            new_path.extend(sorted_group)

        self.influence_path = new_path
        return self.influence_path
    
    def susp_threshold_filter(self, 
        events_susp: List[Tuple[str, int, float]]) -> List[Tuple[str, int, float]]:
        return [x for x in events_susp if x[2] >= self.susp_threshold]

    def get_ranked_candidates(target_func: str, rank: Dict[str, int], ast_tree: ASTNode):
        """Return a list of failure candidates.
        
        The list is sorted by suspiciousness (Ochiai Metric)
        and statistical ranking.

        :param model: The module that holds the bugged program.
        :type  model: ModuleType
        :param target_func: The function that triggers the bugged program.
        :type  target_func: str
        :rtype: InfluencePath
        """
        target = TargetVisitor(target_func, ast_tree)
        calls = CallVisitor(target.func_names, target.target_node)
        target_funcs = FunctionVisitor(calls.call_names, ast_tree)
        _STMT_ALL = set()
        stmt_target = StatementVisitor(rank, target.target_node)
        _STMT_ALL = _STMT_ALL | stmt_target.statements
        for node in target_funcs.func_nodes:
            stmt_nodes = StatementVisitor(rank, node)
            _STMT_ALL = _STMT_ALL | stmt_nodes.statements
        return sorted(_STMT_ALL, key=lambda x: x[2])

    @classmethod
    def get_statistical_ranking(cls) -> Dict[str, int]:
        """ Class Method to return a statistical ranking"""
        return cls.StatisticalRanking

    @staticmethod
    def get_all_func_names(module: ModuleType) -> List[str]:
        """Return a list of the function names found in the provided module.

        :param model: The module that holds the bugged program.
        :type  model: ModuleType
        :rtype: List[str]
        """
        from inspect import getmembers, isfunction, ismethod
        return [func_name for func_name, _ in getmembers(module, isfunction or ismethod)]

    @staticmethod
    def get_model_ast(module: ModuleType) -> ASTNode:
        """Return the abstract syntax tree of the provided module.

        :param model: The module that holds the bugged program.
        :type  model: ModuleType
        :rtype: ASTNode
        """
        from inspect import getsource
        from ast import parse
        src = getsource(module)
        return parse(src)

    def __str__(self) -> str:
        """ Class String representation method """
        return self.__repr__()

    def __repr__(self) -> str:
        """ Class representation method """
        try:
            return super().__repr__()
        except Exception as e:
            return f"GOOD: {e}"

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        """Exit the `with` block.
        
        In case that a timeout is triggered by signal.SIGALRM,
        the event will be detected by the change of value in the
        control variable TIMEOUT_SIGNAL_RECEIVED. If the value
        is equal to 2 the process will label the current test as FAIL,
        add it to a collector and 'consume' the timeout exception.

        """
        status = self.collector.__exit__(exc_tp, exc_value, exc_traceback)
        if status is None:
            pass
        else:
            if DebugController.TIMEOUT_SIGNAL_RECEIVED == 2:
                DebugController.TIMEOUT_SIGNAL_RECEIVED = 0
                outcome = self.FAIL
                self.add_collector(outcome, self.collector)
                return True
            return False  # Internal error; re-raise exception

        if exc_tp is None:
            outcome = self.PASS
        else:
            outcome = self.FAIL

        self.add_collector(outcome, self.collector)
        return True  # Ignore exception, if any

Debugger = AbinDebugger
