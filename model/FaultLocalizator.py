"""
This module contains the FaultLocalizator class.
This class in charge of locate the most suspicious lines of code
that may hold a defect.
This is one of the core modules used to automatically repair a defect.
"""
from model.abstractor.NodeMapper import ASTNode
from model.core.AbinDebugger import Debugger, AbinDebugger, InfluencePath
from model.core.ModelTester import ModelTester, TestSuite
from typing import Tuple, Type, List, Any, Union, Optional, TypeVar
from types import TracebackType
from pathlib import Path
from shutil import rmtree as remove_dir
import ast
import astunparse
import re
import controller.AbinLogging as AbinLogging
import controller.DebugController as DebugController
import signal
signal.signal(signal.SIGALRM, DebugController.test_timeout_handler)

class FaultLocalizator(ModelTester):
    """ This class is used to automatically locate a defective LOC """
    def __init__(self,
        model_path: str, target_function: str, 
        test_suite: TestSuite) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init FaultLocalizator')
        src_code = self.prepare_model(model_path)
        super().__init__(src_code, target_function, test_suite)

    @staticmethod
    def clean_temporal_files(curr_dir: Path) -> None:
        """ This method cleans up the temporal folder """
        with curr_dir.joinpath('temp') as temp_dir:
            if temp_dir.exists():
                remove_dir(temp_dir)
            temp_dir.mkdir(exist_ok=True)

    def prepare_model(self, path) -> str:
        """ This method prepares the provided model/program.

        :rtype: str
        """
        parsed_source = ''
        try:
            with open(path, 'r') as f:
                src = f.read()
        except Exception:
            AbinLogging.debugging_logger.exception(f'Unable to open the file at the given path {path}.')
        else:
            parsed_model = self.parse_model(src)
            parsed_source = astunparse.unparse(parsed_model)
            parsed_source = re.sub('^\n+', '', parsed_source) # Remove new lines at the start of the src code
        finally:
            return parsed_source

    @staticmethod
    def parse_model(src) -> ASTNode:
        """This method refactor the model for the debugging process.
        
        This method removes unnecesary components like docstrings
        and refactor multiple lines' statements into one line statements.

        :rtype: str
        """
        try:
            parsed = ast.parse(src)
        except Exception:
            AbinLogging.debugging_logger.exception(f'Unable to parse the given file.')
        else:
            for node in ast.walk(parsed):
                if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
                    continue
                if not len(node.body):
                    continue
                if not isinstance(node.body[0], ast.Expr):
                    continue
                if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Str):
                    continue
                node.body = node.body[1:]
        finally:
            return parsed