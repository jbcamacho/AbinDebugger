from decimal import DivisionByZero
from model.debugger.AbinDebugger import Debugger, AbinDebugger
from typing import Type, List
from model.FaultLocalizator import FaultLocalizator
from model.FaultLocalizator import Observation, TestCase, PassedTest, FailedTest
from importlib import import_module, reload
from importlib.util import spec_from_file_location

import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)

from enum import Enum
class Behavior(Enum):
    Improvement = 1
    Worsened = 2
    Same = 3
    Correct = 4
    Undefined = 5

class HyphotesisTester(FaultLocalizator):

    def __init__(self, prev_observation: Observation,
                func_name: str,
                model_name: str,
                test_cases: List[TestCase], 
                debugger: Debugger = AbinDebugger) -> None:
        logger.debug('Init HyphotesisTester')
        self.prev_observation = prev_observation
        # [:-3] to remove the '.py' extension from the model_name
        self.model_name = model_name[:-3]
        super().__init__(func_name, '', test_cases, debugger)
        

    def compare_observations(self) -> Type[Behavior]:
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
        explanatory_power = 0
        no_test_cases = len(observation)
        test_outcome = lambda x: True if x[1] == PassedTest else False
        no_passed_test_cases = sum(map(test_outcome, observation))
        try:
            explanatory_power = no_passed_test_cases/no_test_cases
        except DivisionByZero:
            logger.exception("The given observation do not have any test case.")
        finally:
            return explanatory_power
    
    def is_consistent(self) -> bool:
        #Have the same test_cases?
        if len(self.prev_observation) != len(self.observation):
            return False
        
        for prev_test_result, curr_test_result in zip(self.prev_observation, self.observation):
            if prev_test_result[1] == PassedTest and curr_test_result[1] == FailedTest:
                return False
        return True
    
    @staticmethod
    def get_complexity():
        pass

    def __repr__(self) -> str:
        pass

    def __enter__(self):
        logger.debug('Entering HyphotesisTester')
        try:
            self.model = import_module(name=f'..{self.model_name}', package='temp.subpkg')
            self.model = reload(self.model)
            self.func = getattr(self.model, self.func_name, lambda : None)
        except Exception as e:
            logger.exception("An error ocurrer while importing the model.")
            self.model = None
            self.func = None
        return self 