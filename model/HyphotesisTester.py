"""
This module contains the HypothesisTester class.
This class in charge of testing the generated hypotheses.
This is one of the core modules used to automatically repair a defect.
"""
from model.debugger.AbinDebugger import Debugger, AbinDebugger
from model.FaultLocalizator import FaultLocalizator
from model.FaultLocalizator import Observation, TestCase, PassedTest, FailedTest
from typing import Type, List
from importlib import import_module, reload
import controller.AbinLogging as AbinLogging

from enum import Enum
class Behavior(Enum):
    Improvement = 1
    Worsened = 2
    Same = 3
    Correct = 4
    Undefined = 5

class HyphotesisTester(FaultLocalizator):
    """ This class is used to automatically test a hypothesis """
    def __init__(self, prev_observation: Observation,
                func_name: str,
                model_name: str,
                test_cases: List[TestCase], 
                debugger: Debugger = AbinDebugger) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init HyphotesisTester')
        super().__init__(func_name, '', test_cases, debugger)
        self.prev_observation = prev_observation
        self.model_name = model_name[:-3] # [:-3] to remove the '.py' extension from the model_name
        
        

    def compare_observations(self) -> Behavior:
        """ This method compares two observations 
        
        The two observations are compared in order to obtain a behavior,
        the behavior indicates the degree of utility the new tested hypothesis have.

        : type: Behavior
        """
        if self.is_consistent:
            prev_explanatory_power = self.get_explanatory_power(self.prev_observation)
            curr_explanatory_power = self.get_explanatory_power(self.observation)
            if curr_explanatory_power == 1:
                return Behavior.Correct
            elif prev_explanatory_power < curr_explanatory_power:
                return Behavior.Improvement
            elif prev_explanatory_power == curr_explanatory_power:
                return Behavior.Same
        return Behavior.Worsened
    
    @staticmethod
    def get_explanatory_power(observation: Observation) -> int:
        """ This method calculates the explanatory power.

        The explanatory power is the ratio of no. paseed test cases
        and the total number of test cases.

        :param observation: The list of TestResults obtained
        from testing the hypothesis.
        :type  observation: Observation
        : rtype: int
        """
        explanatory_power = 0
        no_test_cases = len(observation)
        test_outcome = lambda x: True if x[1] == PassedTest else False
        no_passed_test_cases = sum(map(test_outcome, observation))
        try:
            explanatory_power = no_passed_test_cases/no_test_cases
        except ZeroDivisionError:
            AbinLogging.debugging_logger.exception(
                "The given observation do not have any test case."
            )
        finally:
            return explanatory_power
    
    def is_consistent(self) -> bool:
        """ This method checks the consistency of two observations.

        This method checks the consistency of the current observation
        agaist the previous observation.

        :rtype: bool
        """
        # Check if have the same number of test_cases?
        if len(self.prev_observation) != len(self.observation):
            return False
        
        for prev_test_result, curr_test_result in zip(self.prev_observation, self.observation):
            if (prev_test_result[1] == PassedTest
                and curr_test_result[1] == FailedTest):
                return False
        return True
    
    @staticmethod
    def get_complexity():
        """ Abstract Method """
        pass

    def __repr__(self) -> str:
        """ Abstract Method """
        pass

    def __enter__(self):
        """ Context manager method used to initialize the defective model/program """
        AbinLogging.debugging_logger.debug('Entering HyphotesisTester')
        try:
            self.model = import_module(
                name=f'..{self.model_name}',
                package='temp.subpkg'
            )
            self.model = reload(self.model)
            self.func = getattr(self.model, self.func_name, lambda : None)
        except Exception as e:
            AbinLogging.debugging_logger.exception(
                "An error ocurred while importing the model."
            )
            self.model = None
            self.func = None
        return self 