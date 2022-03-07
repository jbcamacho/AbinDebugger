"""
This module contains the HypothesisRefinement class.
This class in charge of refining hypotheses to repair a defect.
This is one of the core modules used to automatically repair a defect.
"""
from typing import List, Union
import controller.AbinLogging as AbinLogging
from model.HyphotesisTester import ModelConstructor, TestSuite
from model.core.ModelTester import ModelTester
from model.HypothesisGenerator import Hypothesis, Hypotheses, Iterator

ImprovementCadidates = Iterator[Hypotheses]

from enum import Enum
class AbductionSchema(Enum):
    DFS = 1
    BFS = 2
    A_star = 3

class HypothesisRefinement(ModelTester, ModelConstructor):
    """ This class is used to automatically refine an hypothesis """
    improvement_candidates: ImprovementCadidates
    
    def __init__(self, improvement_candidates: ImprovementCadidates,
        src_code: Union[List[str], str], target_function: str, 
        test_suite: TestSuite, hypothesis: Hypothesis) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init HypothesisRefinement')
        self.improvement_candidates = self.sort_imprv_candidates(improvement_candidates)

        # src_code[:] instances a new variable
        new_model_code = self.build_hypothesis_model(hypothesis, src_code[:]) 
        super().__init__(new_model_code, target_function, test_suite)

    def select_imprv_candidate(self) -> Hypothesis:
        """ This method return the next improvement candidate in the iterator.
        :rtype: int
        """
        return next(self.improvement_candidates)

    @staticmethod
    def sort_imprv_candidates(hypotheses: Hypotheses) -> ImprovementCadidates:
        """ This method sorts the given hypotheses.
        
        The hypotheses will be sorted out by explanatory power
        and turned into a Iterator.
        :rtype: ImprovementCadidates
        """
        # The explanatory power is the third argument of a hypothesis
        improvement_candidates = sorted(hypotheses, key=lambda x: x[2])
        return iter(improvement_candidates)