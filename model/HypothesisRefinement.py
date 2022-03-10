"""
This module contains the HypothesisRefinement class.
This class in charge of refining hypotheses to repair a defect.
This is one of the core modules used to automatically repair a defect.
"""
from typing import Tuple, Iterator
import controller.AbinLogging as AbinLogging
from model.HyphotesisTester import ModelConstructor
from model.HypothesisGenerator import Hypothesis, Hypotheses
from itertools import tee as n_plicate_iterator
ImprovementCadidates = Iterator[Hypotheses]

from enum import Enum
class AbductionSchema(Enum):
    DFS = 1
    BFS = 2
    A_star = 3

class HypothesisRefinement(ModelConstructor):
    """ This class is used to automatically refine an hypothesis """
    improvement_cadidates_set: ImprovementCadidates
    
    def __init__(self, improvement_cadidates_set: ImprovementCadidates,
        schema: AbductionSchema = AbductionSchema.DFS) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init HypothesisRefinement')
        self.improvement_cadidates_set, copy_imprv_cand = self.sort_imprv_candidates(improvement_cadidates_set, schema)
        AbinLogging.debugging_logger.info(f'Improvement Cadidates Set:\n{list(copy_imprv_cand)}')

    def select_imprv_candidate(self) -> Hypothesis:
        """ This method return the next improvement candidate in the iterator.
        :rtype: int
        """
        return next(self.improvement_cadidates_set, None)

    def __iter__(self):
        return self

    def __next__(self):
        return self.select_imprv_candidate()

    @staticmethod
    def sort_imprv_candidates(hypotheses: Hypotheses, 
        schema: AbductionSchema = AbductionSchema.DFS) -> Tuple[ImprovementCadidates, ImprovementCadidates]:
        """ This method sorts the given hypotheses.
        
        The hypotheses will be sorted out by explanatory power
        and turned into a Iterator.
        :rtype: ImprovementCadidates
        """
        improvement_cadidates_set = hypotheses
        if schema == AbductionSchema.A_star:
            # The explanatory power is the third argument of a hypothesis
            improvement_cadidates_set = sorted(hypotheses, key=lambda x: x[2])
        return n_plicate_iterator(improvement_cadidates_set, 2)