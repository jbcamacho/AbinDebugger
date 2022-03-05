"""
This module contains the HypothesisGenerator class.
This class in charge of generating new hypotheses to repaor a defect.
This is one of the core modules used to automatically repair a defect.
"""
from copy import deepcopy
from pathlib import Path
from typing import List, Iterator, Tuple, Union, Type, Optional
from types import TracebackType
from model.abstractor.NodeAbstractor import NodeAbstractor, NodeAbstraction
from model.abstractor.PythonLLOC import PythonLLOC
from model.abstractor.HypothesisAbductor import HypothesisAbductor
from model.abstractor.NodeMapper import ASTNode, IDTokens
import controller.AbinLogging as AbinLogging
import controller.DebugController as DebugController
import re
from pymongo import MongoClient

MatchingPattern = NodeAbstraction
MatchingPatterns = Iterator[MatchingPattern]
Hypothesis = Tuple[str, int, int]
Hypotheses = List[Hypothesis]
class HypothesisGenerator():
    """ This class is used to automatically generate a set of hypotheses """
    abduction_depth: int
    abduction_breadth: int
    complexity: int
    candidate: int
    bug_candidates: Iterator
    hypotheses_set_position: int
    hypotheses_set_complexity: int
    abductor: HypothesisAbductor
    node_abstractor: NodeAbstractor
    bugged_LOC: PythonLLOC
    matching_patterns: MatchingPatterns
    hypotheses_set: Iterator[Hypotheses]
    max_complexity: int
    nested_node: str

    def __init__(self, influence_path: list,
        model_src: Union[List[str], str], max_complexity: int = 3) -> None:
        """ Constructor Method """
        AbinLogging.debugging_logger.debug('Init HypothesisGenerator')
        self.abduction_depth = 0
        self.abduction_breadth = 0
        self.complexity = 0
        self.max_complexity = max_complexity
        self.candidate = 0
        self.bug_candidates = map(lambda candidate: candidate[1], influence_path)
        self.model_src = model_src
        self.matching_patterns = iter([])
        self.hypotheses_set = iter([])
        self.hypotheses_set_complexity = 0
        self.hypotheses_set_position = 0
        self.LogicalLOC = PythonLLOC
        self.abductor = HypothesisAbductor
        self.node_abstractor = NodeAbstractor
        self.nested_node = None

    def get_bug_candidate(self) -> int:
        """ This method return the next bug candidate in the iterator.
        : rtype: int
        """
        return next(self.bug_candidates)

    def abstract_bug_candidate(self, ast_bug_candidate: ASTNode) -> str:
        """ This method return hexdigest of the abstracted node.
        : rtype: str
        """
        bugged_node_abstract = self.node_abstractor(ast_bug_candidate)
        hexdigest = bugged_node_abstract.ast_hexdigest
        return hexdigest

    def get_matching_patterns(self, ast_node_hexdigest: str) -> Tuple[MatchingPatterns, int]:
        """ This method query the database to obtain a list of MatchingPatterns
        
        The hex digest of the abstracted node is used to query
        all identical patterns in the database. The query is an aggregator.

        :param ast_node_hexdigest: the hexdigest of the abstracted node.
        :type  ast_node_hexdigest: str
        : rtype: Tuple[MatchingPatterns, int]
        """
        config = DebugController.DATABASE_SETTINGS
        db_connection = self.mongodb_connection()
        collection_BugPatterns = db_connection[config['COLLECTION']]
        QUERY = [
            { '$match': { 'bug_metadata.hexdigest': ast_node_hexdigest } },
            { '$group': { '_id': '$fix_metadata.hexdigest',
                        'fix_metadata': { '$first': '$fix_metadata' },
                        'bug_metadata': { '$first': '$bug_metadata' },
                        'available_identifiers': { '$first': '$available_identifiers' },
                        'commit_sha': { '$first': '$commit_sha' },
                        'complexity': { '$first': { '$size': { '$objectToArray': "$fix_metadata.map_ids" } } },
                        'count_similar': { '$sum': 1 }
                        }
            },
            { '$sort': { 'complexity': 1 } },
            { '$match': { 'complexity': { '$lte': self.max_complexity } } }
        ]
        matching_patterns = collection_BugPatterns.aggregate(QUERY)
        matching_patterns_count = len(list(matching_patterns))
        matching_patterns = collection_BugPatterns.aggregate(QUERY)
        self.matching_patterns = matching_patterns
        return (matching_patterns, matching_patterns_count)
    
    def apply_bugfix_pattern(self, 
        bugged_node: NodeAbstractor, 
        pattern: MatchingPattern, 
        available_identifiers: IDTokens) -> Iterator[Hypotheses]:
        """ This method apply the fix pattern to the abstracted node.

        This method return a iterator of hypotheses generated
        by the application of the fix pattern.
        
        :param bugged_node: The abstracted node object.
        :type  bugged_node: NodeAbstractor
        :param pattern: The fix pattern.
        :type  pattern: MatchingPattern
        :param available_identifiers: the hexdigest of the abstracted node.
        :type  available_identifiers: IDTokens
        : rtype: Iterator[Hypotheses]
        """
        hypotheses = HypothesisAbductor(bugged_node, pattern, available_identifiers)
        return iter(hypotheses)

    def build_hypothesis_model(self, hypothesis: Hypothesis) -> Union[str, None]:
        """ This methos create a new model to test the given hypothesis.
        
        :param hypothesis: The hypothesis that need a model.
        :type  hypothesis: Hypothesis
        :rtype: Union[str, None]
        """
        new_model_src = self.get_current_model()
        if self.nested_node == 'elif' and re.search('if.*', hypothesis):
            hypothesis = 'el' + hypothesis
        indent = re.split('\w', new_model_src[self.candidate - 1])
        hypothesis = indent[0] + hypothesis + '\n'
        new_model_src[self.candidate - 1] = hypothesis
        
        curr_dir = Path(__file__).parent.parent.resolve()
        new_model_filename = f"model{str(self.abduction_depth+1)}.py"
        new_model_path = curr_dir.joinpath('temp', new_model_filename)
        
        try:
            with open(new_model_path, 'w') as m:
                m.writelines(new_model_src)
        except Exception as e:
            AbinLogging.debugging_logger.exception(f"Unable to parse the new model {new_model_filename}.")
            return None
        #self.abduction_depth += 1
        return hypothesis

    def __iter__(self) -> None:
        """ Class Iterator Constructor """
        return self

    def __next__(self) -> str:
        """ Class Iterator Next Constructor

        This method will iterate over all bug candidates and generate a hypothesis
        until the iterator `self.bug_candidates` is exhausted.
        
        : rtype: str
        """
        hypothesis: Hypothesis = None
        while hypothesis is None:
            try:
                hypothesis = next(self.hypotheses_set)
                if self.nested_node == 'elif' and re.search('if.*', hypothesis):
                    # Check if the hypothesis is part of an elif nested structure
                    hypothesis = 'el' + hypothesis
            except StopIteration:
                pattern: Union[MatchingPattern, None] = None
                while pattern is None:
                    try:
                        pattern = next(self.matching_patterns)
                    except StopIteration:
                        try:
                            self.candidate = self.get_bug_candidate()
                        except StopIteration:
                            msg_ = 'No more bug candidates to abstract. Automatic Program Repair Failed!'
                            AbinLogging.debugging_logger.info(msg_)
                            raise StopIteration(msg_)
                        else:
                            self.abduction_depth = 0
                            # self.abduction_breadth += 1
                            model = self.model_src
                            logical_loc = self.LogicalLOC(self.candidate, '\n'.join(model))
                            ast_bug_candidate = deepcopy(logical_loc.ast_node)
                            ast_hexdigest = self.abstract_bug_candidate(ast_bug_candidate)
                            self.nested_node = logical_loc.get_nested_node()
                            ast_bug_candidate = deepcopy(logical_loc.ast_node)
                            available_identifiers = logical_loc.get_available_identifiers()
                            patterns = self.get_matching_patterns(ast_hexdigest)
                            (self.matching_patterns, count) = patterns
                            AbinLogging.debugging_logger.info(f"""
                            Current Candidate: {self.candidate}. Patterns Found: {count}
                            """
                            )
                
                model = self.model_src
                logical_loc = self.LogicalLOC(self.candidate, '\n'.join(model))
                # print(f'MODEL:\n {model}')
                # print(f'CANDIDATE:\n {self.candidate}')
                # print(f'LLOC:\n {logical_loc.logical_LOC}')
                self.nested_node = logical_loc.get_nested_node()
                ast_bug_candidate = deepcopy(logical_loc.ast_node)
                available_identifiers = logical_loc.get_available_identifiers()
                self.hypotheses_set = self.apply_bugfix_pattern(ast_bug_candidate, pattern, available_identifiers)
                self.hypotheses_set_complexity = pattern['complexity']
                self.hypotheses_set_position = self.candidate
        # hypothesis = self.build_hypothesis_model(hypothesis)
        self.abduction_breadth += 1

        # return ('model1.py', hypothesis)
        return (hypothesis, self.hypotheses_set_position, self.hypotheses_set_complexity)

    def __enter__(self):
        """ Context manager method """
        AbinLogging.debugging_logger.debug('Entering HypothesisGenerator')
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
        AbinLogging.debugging_logger.debug('Exiting HypothesisGenerator')
        AbinLogging.debugging_logger.info(f"""
            <=== Exit Process Data ===>
            Current Candidate: {self.candidate}
            Remaining Candidates: {list(self.bug_candidates)}
            Abduction Depth: {self.abduction_depth}
            Abduction Breadth: {self.abduction_breadth}
            Abduction Complexity: {self.complexity}
            Total Number of Abductions Performed: {self.abduction_depth*self.complexity}
            """
        )
        if exc_tp is not None:
            from traceback import format_exc
            AbinLogging.debugging_logger.warning(f"""
                An error ocurred during the hypotheses generation.
                {exc_tp}: {exc_value}
                Unable to continue the hypotheses generation process.
                """
            )
            AbinLogging.debugging_logger.debug(f"""
                <== Exception Traceback ==>
                """
            )
            AbinLogging.debugging_logger.debug(f"{format_exc()}")
        return True  # Ignore exception, if any

    def get_current_model(self) -> List[str]:
        """ This method return the model source code.
        : rtype: List[str]
        """
        curr_dir = Path(__file__).parent.parent.resolve()
        curr_model_path = curr_dir.joinpath('temp', self.model_name)
        try:
            with open(curr_model_path, 'r') as f:
                model_src = f.readlines()
        except Exception as e:
            AbinLogging.debugging_logger.exception(
                f"Unable to open the file: {self.model_name}."
            )
            return False
        return model_src

    @property
    def model_name(self):
        """ This property represent the current model name"""
        return f"model{str(self.abduction_depth)}.py"

    @property
    def model_path(self):
        curr_dir = Path(__file__).parent.parent.resolve()
        curr_model_path = curr_dir.joinpath('temp', self.model_name)
        return curr_model_path

    @staticmethod
    def mongodb_connection() -> MongoClient:
        """ This method return a connection to the database
        : rtype: MongoClient
        """
        config = DebugController.DATABASE_SETTINGS
        MONGO_URI = f"{config['URI']}://{config['HOST']}:{config['PORT']}"
        client = MongoClient(MONGO_URI)
        db_connection = client[config['DATABASE']]
        return db_connection

