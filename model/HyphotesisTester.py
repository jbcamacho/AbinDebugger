"""
This module contains the HypothesisTester, ModelConstructor and Behaviour classes.
The HypothesisTester class is in charge of testing
the generated hypotheses. This class is one of the core 
modules used to automatically repair a defect.
The ModelConstructor class is in charge of constructing
a proper model for an hypothesis.
The Behaviour class is an enumeration of the available behaviors.
"""
from model.core.ModelTester import ModelTester, TestSuite, Observation, PassedTest, FailedTest
from model.HypothesisGenerator import Hypothesis
from typing import Union, List
import controller.AbinLogging as AbinLogging
import re

from enum import Enum
class Behavior(Enum):
    """ This class represents an enumeration of the currently
    available behaviors; it contains all the behaviors that
    a hypothesis can yield. """
    Improvement = 1
    Worsened = 2
    Same = 3
    Correct = 4
    Undefined = 5
    Valid = 6

class ModelConstructor():
    """ This class contains the methods needed to
    build a hypothesis model."""
    def build_hypothesis_model(self, hypothesis: Hypothesis, 
        src_code: Union[List[str], str]) -> Union[str, None]:
        """ This method create a new model to test the given hypothesis.
        
        :param hypothesis: The hypothesis that need a model.
        :type  hypothesis: Hypothesis
        :rtype: Union[str, None]
        """
        (hypothesis_str, position, *_) = hypothesis
        if isinstance(src_code, str):
            src_code = src_code.splitlines()
        new_model_src = src_code

        indent = re.split('\w', new_model_src[position - 1])
        hypothesis_str = indent[0] + hypothesis_str
        new_model_src[position - 1] = hypothesis_str

        return '\n'.join(new_model_src)
class HyphotesisTester(ModelTester, ModelConstructor):
    """ This class' goal is to test a hypothesis.
    It inherits from ModelTester and ModelConstructor. """
    prev_observation: Observation
    hypothesis: Hypothesis
    def __init__(self, prev_observation: Observation, 
        src_code: Union[List[str], str], target_function: str, 
        test_suite: TestSuite, hypothesis: Hypothesis) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init HyphotesisTester')

        new_model_code = self.build_hypothesis_model(hypothesis, src_code)
        super().__init__(new_model_code, target_function, test_suite)
        self.hypothesis = hypothesis
        self.prev_observation = prev_observation

    def compare_observations(self) -> Behavior:
        """ This method compares two observations.
        
        The two observations are compared in order to obtain a behavior,
        the behavior indicates the degree of utility the new tested hypothesis have.
        Also, this method sets the explanatory power to the given hypothesis.

        :type: Behavior
        """
        if self.is_consistent:
            prev_explanatory_power = self.get_explanatory_power(self.prev_observation)
            AbinLogging.debugging_logger.info(f'Previous Explanatory Power: {prev_explanatory_power}')
            curr_explanatory_power = self.get_explanatory_power(self.observation)
            AbinLogging.debugging_logger.info(f'Current Explanatory Power: {curr_explanatory_power}')
            # The explanatory power is the third argument of a hypothesis.
            self.hypothesis = (*self.hypothesis[:2], curr_explanatory_power)
            if curr_explanatory_power == 1:
                return Behavior.Correct
            elif prev_explanatory_power < curr_explanatory_power:
                return Behavior.Improvement
            elif prev_explanatory_power == curr_explanatory_power:
                return Behavior.Same
        return Behavior.Worsened
    
    @staticmethod
    def get_explanatory_power(observation: Observation) -> float:
        """ This method calculates the explanatory power.

        The explanatory power is the ratio of no. paseed test cases
        and the total number of test cases.

        :param observation: The list of TestResults obtained
        from testing the hypothesis.
        :type  observation: Observation
        :rtype: float
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
            return round(explanatory_power, 4)
    
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