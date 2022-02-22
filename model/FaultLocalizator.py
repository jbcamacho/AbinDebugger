from model.debugger.AbinDebugger import Debugger, AbinDebugger, InfluencePath
from typing import Tuple, Type, List, Any, Union, Optional, TypeVar
from types import TracebackType
import ast, astunparse
from importlib import import_module, reload
from pathlib import Path
from shutil import rmtree as remove_dir

import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)

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
    time_out=3
    influence_path: InfluencePath

    def __init__(self, func_name: str,
                path_bugged_file: str,
                test_cases: List[TestCase],
                debugger: Debugger = AbinDebugger) -> None:
        logger.debug('Init FaultLocalizator')
        self.func_name = func_name
        self.path_bugged_file = path_bugged_file
        self.test_cases = test_cases
        self.debugger = debugger
        self.influence_path: List = []
        self.observation: Observation = []
        self.model = None
        self.func = None

    def __enter__(self) -> Any:
        if self.prepare_bugged_file():
            self.model_name = 'model0'
            try:
                logger.debug('Entering FaultLocalizator')
                self.model = import_module(name=f'..{self.model_name}', package='temp.subpkg')
                self.model = reload(self.model)
                self.func = getattr(self.model, self.func_name, lambda : None)
            except Exception as e:
                #print(f"An error ocurrer while importing the initial model0.\n Error: {e}")
                logger.exception('An error ocurrer while importing the initial model0.')
                self.model = None
                self.func = None
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        logger.debug('Exiting FaultLocalizator')
        """status = self.debugger.__exit__(exc_tp, exc_value, exc_traceback)
        if status is not None:
            return True # Debugger 'AssertionError'; do not raise exception"""
              
        if exc_tp is not None:
            logger.warning("\n\nAn error ocurred during the test.")
            logger.warning(f"{exc_tp}: {exc_value}")
            logger.warning(f"Unable to continue the test of hypothesis model: {self.model_name}")
        return True  # Ignore exception, if any

    def automatic_test(self) -> Tuple[Observation, InfluencePath]:
        new_observation: Observation = [('', FailedTest) for i in range(len(self.test_cases))]
        test_result: ExpectedOutput
        debugger: Debugger = self.debugger()
        for i, test_case, expected_output, *input_args in self.test_cases.itertuples():
            #print('before signal')
            with debugger:
                signal.alarm(1)
                if self.func is None:
                    raise ImportError(f"Failed to import the given function {self.func_name} from the model {self.model_name}.\
                    \nPlease check that the given parameter 'func_name' correspond to a function in the module.")
                test_result = self.func(*input_args)
                logger.debug(f"test_result == expected_output\n{str(test_result)} == {str(expected_output)} ?")
                if str(test_result) == str(expected_output):
                    new_observation[i] = (test_case, PassedTest)
                else:
                    new_observation[i] = (test_case, FailedTest)
                    raise AssertionError(f"The result and the expected output are not equal.\
                        Result: {test_result}\n \
                        Expected: {expected_output}\n"
                    ) 
            signal.alarm(0)
        signal.alarm(0) 
        #print('after signal')
        logger.info(new_observation)
        self.observation = new_observation
        if not self.are_all_test_pass():
            self.influence_path = debugger.get_influence_path(self.model, self.func_name)
        return (self.observation, self.influence_path)

    def run_test(self, input_args) -> ExpectedOutput:
        return self.func(*input_args)
    
    def are_all_test_pass(self):
        return FailedTest not in map(lambda x: x[1], self.observation)

    def prepare_bugged_file(self) -> bool:
        path = self.path_bugged_file
        try:
            with open(path, 'r') as f:
                src = f.read()
        except Exception as e:
            #print(f"Unable to open the file at the given path {path}.\n Error: {e}")
            logger.exception(f'Unable to open the file at the given path {path}.')
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
            #print(f"Unable to parse the given file.\n Error: {e}")
            logger.exception(f'Unable to parse the given file.')
            return False
        return True

    @staticmethod
    def clean_temporal_files(curr_dir: Path) -> None:

        with curr_dir.joinpath('temp') as temp_dir:
            if temp_dir.exists():
                remove_dir(temp_dir)
            temp_dir.mkdir(exist_ok=True)