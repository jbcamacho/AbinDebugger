"""
This module contains the ModelLoader and ModelTester classes.
The ModelLoader class in charge of converting the models into ModuleType objects.
The ModelTester class in charge of automatically test a model.
"""
from model.core.AbinDebugger import Debugger, AbinDebugger, InfluencePath
from types import FunctionType, ModuleType, TracebackType
from typing import Tuple, TypeVar, Type, Union, Optional, Any, List
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
TestSuite = List[TestCase]
Observation = List[TestResult]

from importlib.abc import SourceLoader
from importlib.util import module_from_spec, spec_from_loader
class ModelLoader(SourceLoader):
    """ This class instances a ModuleType object given the source code. 
    This class is a helper class to convert the models into ModuleType objects
    in order test them.
    """
    def __init__(self, src_code) -> None:
        """ Constructor Method """
        super().__init__()
        self.src_code = ''.join(src_code)

    def get_data(self, path) -> bytes:
        """ Abstract method implementation.

        This method is the implementation of the abstract method get_data
        needed to instantiate the SourceLoader class.  This method will instantiate
        the ModuleType object given a src code.

        :param src_code: The source code of the ModuleType object.
        :type  src_code: str
        :rtype: bytes
        """
        return bytes(self.src_code, 'utf-8')
    
    def get_filename(self, fullname: str) -> str:
        """ Abstract method implementation.

        This method is the implementation of the abstract method get_filename
        needed to instantiate the SourceLoader class. This method will name
        the ModuleType object given a fullname.

        :param fullname: The name of the ModuleType object.
        :type  fullname: str
        :rtype: str
        """
        self.fullname = fullname
        return self.fullname
    
    def get_source(self) -> str:
        """ This method will return the source code of the ModuleType object.
        :rtype: str
        """
        return super().get_source(self.fullname)


class ModelTester(ModelLoader):
    """ This class is used to automatically test a model  """
    src_code: Union[List[str], str]
    target_function: str
    test_suite: TestSuite
    model: Union[ModuleType, None]
    func: Union[FunctionType, None]
    influence_path: InfluencePath
    observation: Observation
    debugger: Debugger

    def __init__(self, src_code: Union[List[str], str], 
                target_function: str,
                test_suite: TestSuite, 
                debugger: Debugger = AbinDebugger) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init ModelTester')
        super().__init__(src_code)
        self.target_function = target_function
        self.test_suite = test_suite
        self.func = None
        self.model = None
        self.influence_path = []
        self.observation = []
        self.prev_observation = None
        self.debugger = debugger

    def __enter__(self) -> Any:
        """ Context manager method used to initialize the defective model/program """
        AbinLogging.debugging_logger.debug('Entering ModelTester')
        spec = spec_from_loader(name='model_in_test', loader=self) # The class itself contains the loader
        self.model = module_from_spec(spec)
        try:
            spec.loader.exec_module(self.model)
        except Exception:
            AbinLogging.debugging_logger.exception(
                f'An error ocurred while importing the model {self.model.__name__}'
            )
        else:
            try:
                self.func = getattr(self.model, self.target_function, None)
            except Exception:
                AbinLogging.debugging_logger.exception(
                f'An error ocurred while accesing the target function {self.target_function}'
                )
        finally:
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
        AbinLogging.debugging_logger.debug('Exiting ModelTester')
              
        if exc_tp is not None:
            from traceback import format_exc
            AbinLogging.debugging_logger.warning(f"""
                An error ocurred during the model test.
                {exc_tp}:{exc_value}
                Unable to continue the test of the hypothesis model: {self.model.__name__}
                """
            )
            AbinLogging.debugging_logger.debug(f"""
                <== Exception Traceback ==>
                """
            )
            AbinLogging.debugging_logger.debug(f"{format_exc()}")
        return True  # Ignore exception, if any

    def model_testing(self, check_consistency: bool = False) -> Tuple[Observation, InfluencePath]:
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
        new_observation: Observation = [('UndefinedTest', FailedTest) for i in range(len(self.test_suite))]
        test_result: ExpectedOutput
        debugger: Debugger = self.debugger()
        AbinLogging.debugging_logger.info(f"Starting Model Test...")
        for i, test_case, expected_output, *input_args in self.test_suite.itertuples():
            AbinLogging.debugging_logger.info(f"Testing {test_case}...")
            with debugger:
                signal.setitimer(signal.ITIMER_REAL, DebugController.TEST_TIMEOUT)
                if self.func is None:
                    raise ImportError(f"""
                        Failed to import the given function {self.target_function} from the model {self.model.__name__}.
                        Please check that the given parameter 'func' correspond to a function in the model.
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

            signal.setitimer(signal.ITIMER_REAL, 0)
            if check_consistency and new_observation[i][1] == FailedTest:
                AbinLogging.debugging_logger.debug('check_consistency')
                is_consistent_ = self.check_result_consistency(new_observation[i], i)
                if not is_consistent_:
                    AbinLogging.debugging_logger.debug('break for test inconsistency')
                    break
        
        AbinLogging.debugging_logger.info(f"Model Test Finished...")
        signal.setitimer(signal.ITIMER_REAL, 0) # Make sure the signal.SIGALRM is disabled.
        self.observation = new_observation
        if not self.are_all_test_pass():
            self.influence_path = debugger.get_influence_path(self.model, self.func)
        return (self.observation, self.influence_path)

    def run_test(self, input_args) -> ExpectedOutput:
        """ Dummy Method for futher implementations """
        return self.func(*input_args)

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
            return True # Cannot check consistency if there are not previous observations
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

    def are_all_test_pass(self) -> bool:
        """ This method check if the whole test suite's outcome is PassedTest 
        :rtype: bool
        """
        return FailedTest not in map(lambda x: x[1], self.observation)

    @property
    def model_src(self) -> List[str]:
        """ This property represents the src code of the model.
        The model is represented in a List where each element of sai list
        is a statement of the model in cuestion.
        :rtype: List[str]
        """
        return self.get_source().splitlines()



