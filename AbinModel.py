from typing import List, Type, Optional
from types import TracebackType
from model.FaultLocalizator import FaultLocalizator, TestCase
from model.HyphotesisTester import Behavior, HyphotesisTester
from model.HypothesisGenerator import HypothesisGenerator
import pandas as pd

import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)


Localizator = FaultLocalizator
Tester = HyphotesisTester
Generator = HypothesisGenerator
Refinement = 'HypothesisRefinement'

class AbinModel():

    function_name: str
    bugged_file_path: str
    test_suite: List[TestCase]
    fault_localizator: Localizator
    hyphotesis_tester: Tester
    hypotheses_generator: Generator
    current_behavior: Behavior
    max_complexity: int

    def __init__(self, function_name: str, bugged_file_path: str, test_suite: List[TestCase],
                max_complexity: int = 3,
                localizator: Localizator = FaultLocalizator,
                tester: Tester = HyphotesisTester,
                generator: Generator = HypothesisGenerator) -> None:

        self.function_name = function_name
        self.bugged_file_path = bugged_file_path
        self.test_suite = test_suite
        self.max_complexity = max_complexity
        self.candidate = None
        self.bugfixing_hyphotesis = None

        self.fault_localizator = localizator
        self.hyphotesis_tester = tester
        self.hypotheses_generator = generator
    
    def start_auto_debugging(self):
        (model_name, behavior, prev_observation, influence_path) = self.fault_localization()
        logger.info(f"Observations:\n{prev_observation}")
        logger.info(f"Influence Path by Suspiciousness Ranking:\n{influence_path}")

        #print(f"Observations:\n{prev_observation}")
        #print(f"Influence Path by Suspiciousness Ranking:\n{influence_path}")
        new_observation = []
        if behavior == Behavior.Correct:
            logger.debug(f"\n\nSUCCESSFUL REPAIR!")
            return (model_name, behavior, prev_observation, [])
        hypotheses_generator = self.hypotheses_generation(influence_path)
        with hypotheses_generator:
            for i, (model_name, hypothesis) in enumerate(hypotheses_generator):
                print(f"\nTesting Hypothesis {i}.\nModel {model_name}.\nHypothesis: {hypothesis}")
                logger.info(f"\nTesting Hypothesis {i}.\nModel {model_name}.\nHypothesis: {hypothesis}")
                (behavior, new_observation) = self.hyphotesis_testing(prev_observation, model_name)
                print(f"Behavior Type: {behavior}")
                logger.info(f"Behavior Type: {behavior}")
                if behavior == Behavior.Correct:# or behavior == Behavior.Improvement:
                    logger.debug(f"\nPrevious Observations:\n{prev_observation}\n")
                    logger.debug(f"\nNew Observations:\n{new_observation}\n")
                    logger.debug(f"\n\nSUCCESSFUL REPAIR!")
                    self.candidate = hypotheses_generator.candidate
                    self.bugfixing_hyphotesis = hypothesis
                    return (model_name, behavior, prev_observation, new_observation)
        logger.debug(f"\n\nUNABLE TO REPAIR!")
        return ('', behavior, prev_observation, new_observation)
        

    def fault_localization(self):
        model_name = ''
        behavior = Behavior.Undefined
        prev_observation = []
        influence_path = []
        with self.fault_localizator(self.function_name,
            self.bugged_file_path, self.test_suite) as localizator:
            (prev_observation, influence_path) = localizator.automatic_test()
            model_name = localizator.model_name
            if localizator.are_all_test_pass():
                behavior = Behavior.Correct
        return (model_name, behavior, prev_observation, influence_path)

    def hypotheses_generation(self, influence_path, max_complexity=3):
        return self.hypotheses_generator(influence_path, max_complexity)

    def hyphotesis_testing(self, prev_observation, model_name):
        behavior = Behavior.Undefined
        new_observation = []
        influence_path = []
        with self.hyphotesis_tester(prev_observation, 
            self.function_name, model_name, self.test_suite) as hypo_test:
            (prev_observation, influence_path) = hypo_test.automatic_test()
            behavior = hypo_test.compare_observations()
            new_observation = hypo_test.observation
        return (behavior, new_observation)

    def hyphotesis_refinement(self):
        pass
    
    def __enter__(self):
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        if exc_tp is not None:
            logger.warning("\n\nAn error ocurred during in the model execution.")
            logger.warning(f"{exc_tp}: {exc_value}")
            logger.warning(f"Unable to debug.")
        #return True  # Ignore exception, if any

def parse_csv_data(data):
  from json import loads
  parsed_data = pd.DataFrame()
  parsed_types = []
  columnsNames = list(data.columns)
  parsed_data[columnsNames[0]] = data[columnsNames[0]] # test_cases
  parsed_data[columnsNames[1]] = data[columnsNames[1]] # expected_output
  columnsNames = columnsNames[2:] # skip test_cases and expected_output columns
  for colName in columnsNames:
    newColName, castType = map(str.strip, colName.split(':'))
    #print(newColName, castType)
    parsed_types.append({ 'input_args': newColName, 'type': castType })
    if castType in ['int', 'float', 'str']:
      parsed_data[newColName] = data[colName].map(getattr(__builtins__, castType))
    elif castType in ['dict', 'json']:
      parsed_data[newColName] = data[colName].apply(loads)
    elif castType == 'list':
      parsed_data[newColName] = data[colName].to_list()
    elif castType == 'tuple':
      parsed_data[newColName] = tuple(data[colName].to_list())
  return (parsed_data, pd.DataFrame(parsed_types))

def main():
    from pathlib import Path
    curr_dir = Path(__file__).parent.resolve()
    
    #path_bugged_file = curr_dir.joinpath("benchmarks", "benchmark0.py")
    #df = pd.read_csv(curr_dir.joinpath("benchmarks", "benchmark0.csv"), keep_default_na=False)
    #func_name = 'get_profit'

    #path_bugged_file = curr_dir.joinpath("benchmarks", "benchmark1.py")
    #df = pd.read_csv(curr_dir.joinpath("benchmarks", "benchmark1.csv"), keep_default_na=False)
    #func_name = 'remove_html_markup'

    #path_bugged_file = curr_dir.joinpath("benchmarks", "benchmark2.py")
    #df = pd.read_csv(curr_dir.joinpath("benchmarks", "benchmark2.csv"), keep_default_na=False)
    #func_name = 'middle'

    path_bugged_file = curr_dir.joinpath("benchmarks", "benchmark3.py")
    df = pd.read_csv(curr_dir.joinpath("benchmarks", "benchmark3.csv"), keep_default_na=False)
    func_name = 'check_password_strength'

    (parsed_data, parsed_types) = parse_csv_data(df)
    test_cases = parsed_data
    
    abin = AbinModel(func_name, path_bugged_file, test_cases)
    (model_name, behavior, prev_observation, new_observation) = abin.start_auto_debugging()
    print(model_name)

def debugger_is_active() -> bool:
    import sys
    """Return if the debugger is currently active"""
    gettrace = getattr(sys, 'gettrace', lambda : None) 
    return gettrace() is not None

if __name__ == "__main__":
    
    if debugger_is_active():
        print('The program is currenly being execute in debug mode.')
    else:
        main()