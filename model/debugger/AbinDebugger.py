from model.debugger.Collector import CoverageCollector
from model.debugger.StatisticalDebugger import OchiaiDebugger, Debugger
from typing import Union, Tuple, Type, List, Dict


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
    
    def __init__(self, collector_class: Type = CoverageCollector, log: bool = False):
        super().__init__(collector_class, log)
        self.influence_path: List = []

    def get_influence_path(self, model) -> InfluencePath:
        """Return a list of events, sorted by suspiciousness, highest first."""
        if model is None: return []
        func_names = self.get_all_func_names(model)
        self.influence_path = list(filter(lambda x: x[0] in func_names, self.rank()))
        #self.influence_path = list(filter(lambda x: x[0] not in ['debug', 'isEnabledFor', 'run_test'], self.rank()))
        if self.influence_path:
            return self.influence_path
        else:
            pass
    
    def get_ranked_candidates(self, target_func):
        pass

    @staticmethod
    def get_all_func_names(module) -> list:
        from inspect import getmembers, isfunction, ismethod
        return [func_name for func_name, _ in getmembers(module, isfunction or ismethod)]

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        try:
            return super().__repr__()
        except Exception as e:
            return f"GOOD: {e}"


Debugger = Union[AbinDebugger, Debugger]
