"""
This module is the model of the system.
This is the model representation of the MVC software pattern.
"""
import sys
from typing import List, Type, Optional, Tuple
from types import TracebackType
from model.FaultLocalizator import FaultLocalizator, TestCase, Observation, InfluencePath
from model.HyphotesisTester import Behavior, HyphotesisTester
from model.HypothesisGenerator import HypothesisGenerator
import pandas as pd
import controller.AbinLogging as AbinLogging


Localizator = FaultLocalizator
Tester = HyphotesisTester
Generator = HypothesisGenerator
Refinement = 'HypothesisRefinement'

class AbinModel():
    """ This class is the encapsulation of the model"""
    function_name: str
    bugged_file_path: str
    test_suite: List[TestCase]
    fault_localizator: Localizator
    hyphotesis_tester: Tester
    hypotheses_generator: Generator
    current_behavior: Behavior
    max_complexity: int
    candidate: int
    bugfixing_hyphotesis: str

    def __init__(self, function_name: str, bugged_file_path: str, test_suite: List[TestCase],
                max_complexity: int = 3,
                localizator: Localizator = FaultLocalizator,
                tester: Tester = HyphotesisTester,
                generator: Generator = HypothesisGenerator) -> None:
        """ Constructor Method """
        self.function_name = function_name
        self.bugged_file_path = bugged_file_path
        self.test_suite = test_suite
        self.max_complexity = max_complexity
        self.candidate = None
        self.bugfixing_hyphotesis = None
        self.fault_localizator = localizator
        self.hyphotesis_tester = tester
        self.hypotheses_generator = generator
    
    def start_auto_debugging(self) -> Tuple[str, Behavior, Observation, Observation]:
        """ This method encapsulates the whole debugging process.
        :rtype: Tuple[str, Behavior, Observation, Observation]
        """
        (model_name, behavior, prev_observation, influence_path) = self.fault_localization()
        AbinLogging.debugging_logger.info(f"""
            Observations:
            {prev_observation}
            Influence Path by Suspiciousness Ranking:
            {influence_path}
            """
        )
        new_observation = []
        if behavior == Behavior.Correct:
            AbinLogging.debugging_logger.debug(f"\nSUCCESSFUL REPAIR!")
            return (model_name, behavior, prev_observation, [])
        hypotheses_generator = self.hypotheses_generation(influence_path)
        with hypotheses_generator:
            for i, (model_name, hypothesis) in enumerate(hypotheses_generator):
                AbinLogging.debugging_logger.info(f"""
                    Testing Hypothesis {i}.
                    Model {model_name}.
                    Hypothesis: {hypothesis}
                    """
                )
                (behavior, new_observation) = self.hyphotesis_testing(prev_observation, model_name)
                AbinLogging.debugging_logger.info(f""" 
                    New Observations:
                    {new_observation}
                    Behavior Type:
                    {behavior}
                    """
                )
                if behavior == Behavior.Correct:# or behavior == Behavior.Improvement:
                    AbinLogging.debugging_logger.debug(f""" 
                        Previous Observations:
                        {prev_observation}
                        New Observations:
                        {new_observation}
                        \nSUCCESSFUL REPAIR!
                        """
                    )
                    self.candidate = hypotheses_generator.candidate
                    self.bugfixing_hyphotesis = hypothesis
                    return (model_name, behavior, prev_observation, new_observation)
        AbinLogging.debugging_logger.debug(f"\nUNABLE TO REPAIR!")
        return ('', behavior, prev_observation, new_observation)
        
    def fault_localization(self) -> Tuple[str, Behavior, Observation, InfluencePath]:
        """ This method encapsulates the fault localization process.
        : rtype: Tuple[str, Behavior, Observation, InfluencePath]
        """
        model_name = ''
        behavior = Behavior.Undefined
        prev_observation = []
        influence_path = []
        with self.fault_localizator(self.function_name,
            self.bugged_file_path, self.test_suite) as localizator:
            (prev_observation, influence_path) = localizator.automatic_test(check_consistency=False)
            model_name = localizator.model_name
            if localizator.are_all_test_pass():
                behavior = Behavior.Correct
        return (model_name, behavior, prev_observation, influence_path)

    def hypotheses_generation(self, 
        influence_path: InfluencePath, 
        max_complexity: int = 3) -> Generator:
        """ This method encapsulates the hypotheses generation process.

        :param influence_path: The visited node
        :type  influence_path: InfluencePath
        :param max_complexity: The maximun hypothesis' complexity allowed.
        :type  max_complexity: int
        :rtype : Tuple[Behavior, Observation]
        """
        return self.hypotheses_generator(influence_path, max_complexity)

    def hyphotesis_testing(self, 
        prev_observation: Observation, 
        model_name: str) -> Tuple[Behavior, Observation]:
        """ This method encapsulates the hypothesis testing process.
        
        :param prev_observation: The previous observation.
        :type  prev_observation: Observation
        :param model_name: The model's name.
        :type  model_name: str
        :rtype : Tuple[Behavior, Observation]
        """
        behavior = Behavior.Undefined
        new_observation = []
        influence_path = []
        with self.hyphotesis_tester(prev_observation, 
            self.function_name, model_name, self.test_suite) as hypo_test:
            (prev_observation, influence_path) = hypo_test.automatic_test(check_consistency=True)
            behavior = hypo_test.compare_observations()
            new_observation = hypo_test.observation
        return (behavior, new_observation)

    def hyphotesis_refinement(self):
        pass
    
    def __enter__(self):
        """ Context manager method """
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        """ Context manager method to re-raise exceptions that happened during the process.
        
        :param exc_tp: Type of the raised exception.
        :type  exc_tp: Type
        :param exc_value: The raised exception object.
        :type  exc_value: BaseException
        :param exc_traceback: The trace-back object of the exception.
        :type  exc_traceback: TracebackType
        :rtype: bool
        """
        if exc_tp is not None:
            AbinLogging.debugging_logger.warning(f"""
                An error ocurred during in the model execution.
                {exc_tp}: {exc_value}
                Unable to debug.
                """
            )
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

def debugger_is_active() -> bool:
    """ This method return if the debugger is currently active """
    gettrace = getattr(sys, 'gettrace', lambda : None) 
    return gettrace() is not None

if __name__ == "__main__":
    
    if debugger_is_active():
        print('The program is currenly being execute in debug mode.')
    else:
        main()