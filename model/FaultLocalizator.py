"""
This module contains the FaultLocalizator class.
This class in charge of locate the most suspicious lines of code
that may hold a defect.
This is one of the core modules used to automatically repair a defect.
"""
from model.debugger.AbinDebugger import Debugger, AbinDebugger, InfluencePath
from typing import Tuple, Type, List, Any, Union, Optional, TypeVar
from types import TracebackType
from importlib import import_module, reload
from pathlib import Path
from shutil import rmtree as remove_dir
import ast
import astunparse
import controller.AbinLogging as AbinLogging
import controller.DebugController as DebugController
import signal
signal.signal(signal.SIGALRM, DebugController.test_timeout_handler)


Test = Any
PassedTest = TypeVar('PassedTest')
FailedTest = TypeVar('FailedTest')
TestOutcome = Union[PassedTest, FailedTest]
TestResult = Tuple[Test, TestOutcome]
InputArgs = Any
ExpectedOutput = Any
TestCase = Tuple[Test, InputArgs, ExpectedOutput]
Observation = List[TestResult]

class FaultLocalizator():
    """ This class is used to automatically locate a defective LOC """
    time_out=3
    influence_path: InfluencePath

    def __init__(self, func_name: str,
                path_bugged_file: str,
                test_cases: List[TestCase],
                debugger: Debugger = AbinDebugger) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init FaultLocalizator')
        self.func_name = func_name
        self.path_bugged_file = path_bugged_file
        self.test_cases = test_cases
        self.debugger = debugger
        self.influence_path: List = []
        self.observation: Observation = []
        self.model = None
        self.func = None
        self.prev_observation = None

    def __enter__(self) -> Any:
        """ Context manager method used to initialize the defective model/program """
        if self.prepare_bugged_file():
            AbinLogging.debugging_logger.debug('Entering FaultLocalizator')
            self.model_name = 'model0'
            try:
                self.model = import_module(name=f'..{self.model_name}', package='temp.subpkg')
                self.model = reload(self.model)
                self.func = getattr(self.model, self.func_name, lambda : None)
            except Exception as e:
                AbinLogging.debugging_logger.exception(
                    'An error ocurred while importing the initial model0.'
                )
                self.model = None
                self.func = None
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        """ Context manager method to ignore/consume all the exceptions.
        
        This method is used to void a raising exception that occurred
        during the execution of the class methods.

        :param exc_tp: Type of the raised exception.
        :type  exc_tp: Type
        :param exc_value: The raised exception object.
        :type  exc_value: BaseException
        :param exc_traceback: The trace-back object of the exception.
        :type  exc_traceback: TracebackType
        :rtype: bool
        """
        AbinLogging.debugging_logger.debug('Exiting FaultLocalizator')
              
        if exc_tp is not None:
            from traceback import format_exc
            AbinLogging.debugging_logger.warning(f"""
                An error ocurred during the test.
                {exc_tp}:{exc_value}
                Unable to continue the test of hypothesis model: {self.model_name}
                """
            )
            AbinLogging.debugging_logger.debug(f"""
                <== Exception Traceback ==>
                """
            )
            AbinLogging.debugging_logger.debug(f"{format_exc()}")
        return True  # Ignore exception, if any

    def automatic_test(self, check_consistency: bool = False) -> Tuple[Observation, InfluencePath]:
        """ This method returns an observation of the executed test cases and a inflience path.
        
        
        This method test all the test cases against the provided model.
        Also, it feed a debugger that relies on the statistical analisis 
        of the observed events during the execution of the test cases
        to automatically detect the most suspicios LOC that may hold the defect.
        
        
        :param check_consistency: A control variable to enter
        to the check_result_consistency method.
        :type  check_consistency: bool
        :rtype: Tuple[Observation, InfluencePath]
        """
        new_observation: Observation = [('UndefinedTest', FailedTest) for i in range(len(self.test_cases))]
        test_result: ExpectedOutput
        debugger: Debugger = self.debugger()
        AbinLogging.debugging_logger.info(f"Starting Automatic Test")
        for i, test_case, expected_output, *input_args in self.test_cases.itertuples():
            AbinLogging.debugging_logger.info(f"Testing {test_case}...")
            with debugger:
                signal.alarm(DebugController.TEST_TIMEOUT)
                if self.func is None:
                    raise ImportError(f"""
                        Failed to import the given function {self.func_name} from the model {self.model_name}.
                        Please check that the given parameter 'func_name' correspond to a function in the module.
                        """
                    )
                test_result = self.func(*input_args)
                AbinLogging.debugging_logger.debug(f"""
                    test_result == expected_output
                    {str(test_result)} == {str(expected_output)}?
                    """
                )
                if str(test_result) == str(expected_output):
                    new_observation[i] = (test_case, PassedTest)
                else:
                    new_observation[i] = (test_case, FailedTest)
                    raise AssertionError(f"""
                        The result and the expected output are not equal.
                        Result: {test_result}
                        Expected: {expected_output}
                        """
                    )
            signal.alarm(0)
            if check_consistency and new_observation[i][1] == FailedTest:
                AbinLogging.debugging_logger.debug('check_consistency')
                is_consistent_ = self.check_result_consistency(new_observation[i], i)
                if not is_consistent_:
                    AbinLogging.debugging_logger.debug('break')
                    break
            
        signal.alarm(0) # Make sure the signal is properly disabled before return
        self.observation = new_observation
        if not self.are_all_test_pass():
            self.influence_path = debugger.get_influence_path(self.model, self.func_name)
        return (self.observation, self.influence_path)

    def run_test(self, input_args) -> ExpectedOutput:
        """ Dummy Method for futher implementations """
        return self.func(*input_args)
    
    def are_all_test_pass(self) -> bool:
        """ This method check if the whole test suite's outcome is PassedTest 
        :rtype: bool
        """
        return FailedTest not in map(lambda x: x[1], self.observation)

    def prepare_bugged_file(self) -> bool:
        """ This method prepares the provided model/program to be used by the class itself.
        :rtype: bool
        """
        path = self.path_bugged_file
        try:
            with open(path, 'r') as f:
                src = f.read()
        except Exception as e:
            AbinLogging.debugging_logger.exception(f'Unable to open the file at the given path {path}.')
            return False
        else:
            curr_dir = Path(__file__).parent.parent.resolve()
            self.clean_temporal_files(curr_dir)
        try:
            tree = ast.parse(src)
            parsed_source = astunparse.unparse(tree)
            bugged_model_path = curr_dir.joinpath('temp', 'model0.py')
            with open(bugged_model_path, 'w') as m:
                m.write(parsed_source)
        except Exception as e:
            AbinLogging.debugging_logger.exception(f'Unable to parse the given file.')
            return False
        return True

    def check_result_consistency(self, 
                            curr_test_result: TestResult, 
                            test_case_id: int) -> bool:
        """ This method checks the consistency of two test cases.

        This method checks the consistency of the current test case
        agaist the same test case observed in a previous observation.

        :param curr_test_result: Current test case.
        :type  curr_test_result: TestResult
        :param test_case_id: Current test case identifier.
        :type  test_case_id: int
        :rtype: bool
        """
        if self.prev_observation is None:
            return True # Cannot check consistency if there not previous observations
        prev_test_result = self.prev_observation[test_case_id]
        if (prev_test_result[1] == PassedTest
            and curr_test_result[1] == FailedTest):
            AbinLogging.debugging_logger.info(f"""
                The current test{test_case_id + 1} result is inconsistent with the previous test{test_case_id + 1} result.
                Previous Result: {prev_test_result}
                Current Result: {curr_test_result}
                """
            )
            return False
    
        return True

    @staticmethod
    def clean_temporal_files(curr_dir: Path) -> None:
        """ This method cleans up the temporal folder """
        with curr_dir.joinpath('temp') as temp_dir:
            if temp_dir.exists():
                remove_dir(temp_dir)
            temp_dir.mkdir(exist_ok=True)