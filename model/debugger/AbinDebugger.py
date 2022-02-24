from model.debugger.AbinCollector import AbinCollector
from model.debugger.StatisticalDebugger import OchiaiDebugger, Debugger
from typing import Union, Tuple, Type, List, Dict, Optional
from types import TracebackType
from ast import AST
from model.abstractor.Visitors import TargetVisitor, CallVisitor, FunctionVisitor, StatementVisitor
import controller.DebugController as DebugController

InfluencePath = List[Tuple[str, int]]

class AbinDebugger(OchiaiDebugger):
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
    
    def __init__(self, collector_class: Type = AbinCollector, log: bool = False):
        super().__init__(collector_class, log)
        self.influence_path: List = []

    def get_influence_path(self, model, target_func) -> InfluencePath:
        """Return a list of events, sorted by suspiciousness, highest first."""
        if model is None: return []
        func_names = self.get_all_func_names(model)
        self.influence_path = list(filter(lambda x: x[0] in func_names, self.rank()))
        #self.influence_path = list(filter(lambda x: x[0] not in ['debug', 'isEnabledFor', 'run_test'], self.rank()))
        return self.influence_path
        # if self.influence_path:
        #     return self.influence_path
        # rank = self.get_statistical_ranking()
        # ast_tree = self.get_model_ast(model)
        # candidates = self.get_ranked_candidates(target_func, rank, ast_tree)
        # self.influence_path = list(map(lambda x: (x[1], x[0]), candidates))
        # return self.influence_path
    
    def get_ranked_candidates(target_func, rank, ast_tree):
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
    def get_statistical_ranking(cls):
        return cls.StatisticalRanking

    @staticmethod
    def get_all_func_names(module) -> list:
        from inspect import getmembers, isfunction, ismethod
        return [func_name for func_name, _ in getmembers(module, isfunction or ismethod)]

    @staticmethod
    def get_model_ast(module) -> AST:
        from inspect import getsource
        from ast import parse
        src = getsource(module)
        return parse(src)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        try:
            return super().__repr__()
        except Exception as e:
            return f"GOOD: {e}"

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        """Exit the `with` block."""
        status = self.collector.__exit__(exc_tp, exc_value, exc_traceback)
        if status is None:
            pass
        else:
            if DebugController.TIMEOUT_SIGNAL_RECEIVED == 2:
                DebugController.TIMEOUT_SIGNAL_RECEIVED = 0
                outcome = self.FAIL
                self.add_collector(outcome, self.collector)
                #print('__exit__:DEBUG_SINAL_RECEIVED')
                return True
            return False  # Internal error; re-raise exception

        if exc_tp is None:
            outcome = self.PASS
        else:
            outcome = self.FAIL

        self.add_collector(outcome, self.collector)
        return True  # Ignore exception, if any

Debugger = Union[AbinDebugger, Debugger]
