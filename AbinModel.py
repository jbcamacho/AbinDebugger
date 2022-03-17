"""
This module is the model of the system.
This is the model representation of the MVC software pattern.
"""
import sys
from typing import List, Type, Optional, Tuple, Union
from types import TracebackType
from model.core.ModelTester import TestCase, Observation, InfluencePath
from model.FaultLocalizator import FaultLocalizator
from model.HyphotesisTester import Behavior, HyphotesisTester
from model.HypothesisGenerator import Hypothesis, HypothesisGenerator
from model.HypothesisRefinement import AbductionSchema
import pandas as pd
import controller.AbinLogging as AbinLogging
import controller.DebugController as DebugController

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
                max_complexity: int, abduction_schema: AbductionSchema = AbductionSchema.DFS,
                localizator: Localizator = FaultLocalizator,
                tester: Tester = HyphotesisTester,
                generator: Generator = HypothesisGenerator) -> None:
        """ Constructor Method """
        self.function_name = function_name
        self.bugged_file_path = bugged_file_path
        self.test_suite = test_suite
        self.max_complexity = max_complexity
        self.abduction_depth = 0
        self.abduction_breadth = 0
        self.abduction_schema = abduction_schema
        self.candidate = None
        self.bugfixing_hyphotesis = None
        self.fault_localizator = localizator
        self.hyphotesis_tester = tester
        self.hypotheses_generator = generator
        DebugController.QT_QUEUE.enqueue(self.abduction_breadth, self.abduction_depth)
    
    def start_auto_debugging(self, model_src_code = None,
        improvement_candidates_set = None) -> Tuple[str, Behavior, Observation, Observation]:
        """ This method encapsulates the whole debugging process.
        :rtype: Tuple[str, Behavior, Observation, Observation]
        """
        AbinLogging.debugging_logger.info(f"""
        Schema: {self.abduction_schema}
        Abduction Depth: {self.abduction_depth}
        Abduction Breadth: {self.abduction_breadth}""")
        localizator = self.fault_localization(model_src_code, improvement_candidates_set)
        behavior = Behavior.Undefined
        with localizator:
            (prev_observation, influence_path) = localizator.model_testing(check_consistency=False)
            model_src_code = localizator.model_src
            if localizator.are_all_test_pass():
                behavior = Behavior.Valid
        AbinLogging.debugging_logger.info(f"""
                Observations:
                {prev_observation}
                Influence Path by Suspiciousness Ranking:
                {influence_path}
                """
        )
        if behavior == Behavior.Valid:
            AbinLogging.debugging_logger.info(f"AbinDebugger did not detect any defects in the program.")
            return (model_src_code, behavior, prev_observation, [])
        # We need to save the prev_observation in case of failed refinement
        prev_observation_holder = prev_observation[:]
        imprv_candidates = []
        while True:
            new_observation = []
            hypotheses_generator = self.hypotheses_generation(influence_path, model_src_code[:], self.max_complexity)
            
            with hypotheses_generator:
                for hypothesis in hypotheses_generator:
                    AbinLogging.debugging_logger.info(f"""
                        Testing Hypothesis {self.abduction_breadth}.
                        Hypothesis: {hypothesis}
                        """
                    )
                    self.abduction_breadth += 1
                    DebugController.QT_QUEUE.enqueue(self.abduction_breadth, self.abduction_depth)
                    (new_model_src_code, behavior, new_observation, hypothesis) = self.hyphotesis_testing(prev_observation, model_src_code[:], hypothesis)
                    AbinLogging.debugging_logger.info(f""" 
                        New Observations:
                        {new_observation}
                        Behavior Type:
                        {behavior}
                        """
                    )
                    
                    if behavior == Behavior.Improvement:
                        imprv_candidates.append(hypothesis)
                        if self.abduction_schema == AbductionSchema.DFS:
                            # recursion here
                            self.abduction_depth += 1
                            result = self.start_auto_debugging(model_src_code[:], imprv_candidates)
                            (new_model_src_code, behavior, prev_observation, new_observation) = result
                            imprv_candidates.clear()
                        elif self.abduction_schema == AbductionSchema.BFS:
                            # save hypothesis here
                            pass
                        elif self.abduction_schema == AbductionSchema.A_star:
                            # insertion sort and save hypothesis here
                            # already implemented in refinement class
                            pass
                        

                    if behavior == Behavior.Correct:
                        break
            
            if (imprv_candidates
                and (self.abduction_schema == AbductionSchema.BFS
                or self.abduction_schema == AbductionSchema.A_star) ):
                # recursion here
                self.abduction_depth += 1
                result = self.start_auto_debugging(model_src_code[:], imprv_candidates)
                (new_model_src_code, behavior, prev_observation, new_observation) = result
                imprv_candidates.clear()

            if behavior == Behavior.Correct:
                AbinLogging.debugging_logger.debug(f""" 
                    Previous Observations:
                    {prev_observation}
                    New Observations:
                    {new_observation}
                    Abduction Depth: {self.abduction_depth}
                    Abduction Breadth: {self.abduction_breadth}
                    \nSUCCESSFUL REPAIR!
                    """
                )
                self.candidate = hypotheses_generator.candidate
                self.bugfixing_hyphotesis = hypothesis[0]
                return (new_model_src_code, behavior, prev_observation, new_observation)

            if localizator.is_refinement:
                AbinLogging.debugging_logger.info(f"\nImprovement Candidate Rejected...")
                self.abduction_depth -= 1
                has_imprv_cand = next(localizator)
                if not has_imprv_cand:
                    # We need to return the prev_observation that was saved
                    prev_observation = prev_observation_holder[:]
                    behavior = Behavior.Undefined
                    AbinLogging.debugging_logger.info(f"Failed Refinement...")
                    AbinLogging.debugging_logger.info(f"""
                    Schema: {self.abduction_schema}
                    Abduction Depth: {self.abduction_depth}
                    Abduction Breadth: {self.abduction_breadth}""")
                    return ('', behavior, prev_observation, new_observation)
                behavior = Behavior.Undefined
                with localizator:
                    (prev_observation, influence_path) = localizator.model_testing(check_consistency=False)
                    model_src_code = localizator.model_src
            else:
                break
                

        if self.abduction_depth == 0:
            AbinLogging.debugging_logger.debug(f"\nUNABLE TO REPAIR!")
        return ('', behavior, prev_observation, new_observation)
    
    def fault_localization(self, model_src_code = None, 
        improvement_candidates_set = None) -> Localizator:
        """ This method encapsulates the fault localization process.
        : rtype: Tuple[str, Behavior, Observation, InfluencePath]
        """
        if improvement_candidates_set is None:
            localizator = self.fault_localizator(model_path = self.bugged_file_path,
                target_function = self.function_name, 
                test_suite = self.test_suite,
                schema=self.abduction_schema)
        else:
            AbinLogging.debugging_logger.debug(f"Improvement Candidates: {improvement_candidates_set}\n")
            AbinLogging.debugging_logger.debug(f"New Model: {model_src_code}")
            localizator = self.fault_localizator(src_code = model_src_code,
                improvement_candidates_set = improvement_candidates_set, 
                target_function = self.function_name,
                test_suite = self.test_suite,
                schema=self.abduction_schema)
        return localizator

    def hypotheses_generation(self, 
        influence_path: InfluencePath, 
        src_code: Union[List[str], str],
        max_complexity: int = 3) -> Generator:
        """ This method encapsulates the hypotheses generation process.

        :param influence_path: The visited node
        :type  influence_path: InfluencePath
        :param max_complexity: The maximun hypothesis' complexity allowed.
        :type  max_complexity: int
        :rtype : Tuple[Behavior, Observation]
        """
        return self.hypotheses_generator(influence_path, src_code, max_complexity)

    def hyphotesis_testing(self, 
        prev_observation: Observation, 
        src_code: Union[List[str], str],
        hypothesis: Hypothesis) -> Tuple[Behavior, Observation]:
        """ This method encapsulates the hypothesis testing process.
        
        :param prev_observation: The previous observation.
        :type  prev_observation: Observation
        :param model_name: The model's name.
        :type  model_name: str
        :rtype : Tuple[Behavior, Observation]
        """
        behavior = Behavior.Undefined
        observation = []
        influence_path = []
        new_model_src_code = []
        with self.hyphotesis_tester(prev_observation, src_code,
            self.function_name, self.test_suite, hypothesis) as hypo_test:
            (observation, influence_path) = hypo_test.model_testing(check_consistency=True)
            behavior = hypo_test.compare_observations()
            new_model_src_code = hypo_test.model_src
            hypothesis = hypo_test.hypothesis
        return (new_model_src_code, behavior, observation, hypothesis)

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