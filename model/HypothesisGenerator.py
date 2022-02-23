from copy import deepcopy
from pathlib import Path
import pymongo
from typing import List, Iterator, Tuple, Union, Type, Optional
from types import TracebackType
import re
from model.abstractor.NodeAbstractor import NodeAbstractor
from model.abstractor.PythonLLOC import PythonLLOC, LogicalLOC
from model.abstractor.HypothesisAbductor import HypothesisAbductor
from model.abstractor.Bugfix import BugfixMetadata
from model.abstractor.RecursiveVisitor import ASTNode

import logging
from controller.AbinLogging import LOGGER_LEVEL, CONSOLE_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(CONSOLE_HANDLER)

import controller.DebugController as DebugController

USER = 'readOnlyUser'
PWD = 'houIAX5DHvAYMADw'
DEFAULT_DB = 'Bugfixes'

MatchingPatterns = Iterator[BugfixMetadata]
Hypothesis = str
Hypotheses = List[Hypothesis]

class HypothesisGenerator():
    
    abduction_depth: int
    abduction_breadth: int
    complexity: int
    candidate: int
    bug_candidates: Iterator
    remaining_LLOCs: List[int]
    abductor: HypothesisAbductor
    node_abstractor: NodeAbstractor
    bugged_LOC: PythonLLOC
    matching_patterns: MatchingPatterns
    hypotheses_set: Iterator[Hypotheses]
    max_complexity: int

    def __init__(self, influence_path: list, max_complexity: int = 3) -> None:
        self.abduction_depth = 0
        self.abduction_breadth = 0
        self.complexity = 0
        self.max_complexity = max_complexity
        self.candidate = 0
        self.bug_candidates = map(lambda candidate: candidate[1], influence_path)

        #SHORT#SHORT
        #self.bug_candidates = iter(list(self.bug_candidates)[:3])
        #SHORT#SHORT

        self.matching_patterns = iter([])
        self.hypotheses_set = iter([])
        self.remaining_LLOCs = []
        self.LogicalLOC = PythonLLOC
        self.abductor = HypothesisAbductor
        self.node_abstractor = NodeAbstractor

    def get_bug_candidate(self) -> int:
        return next(self.bug_candidates)

    def abstract_bug_candidate(self, ast_bug_candidate: ASTNode) -> str:
        bugged_node_abstract = self.node_abstractor(ast_bug_candidate)
        hexdigest = bugged_node_abstract.ast_hexdigest
        return hexdigest

    def get_matching_patterns(self, ast_node_hexdigest: str) -> Tuple[MatchingPatterns, int]:
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
    
    def apply_bugfix_pattern(self, bugged_node, pattern, available_identifiers) -> Iterator[Hypotheses]:
        hypotheses = HypothesisAbductor(bugged_node, pattern, available_identifiers)
        return iter(hypotheses)

    def build_hypothesis_model(self, hypothesis: Hypothesis) -> None:
        
        new_model_src = self.get_current_model()
        
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
            logger.exception(f"Unable to parse the new model {new_model_filename}.")
            return False
        #self.abduction_depth += 1
        return True

    def __iter__(self) -> None:
        return self

    def __next__(self) -> str:
        hypothesis: Hypothesis = None
        while hypothesis is None:
            try:
                hypothesis = next(self.hypotheses_set)
            except StopIteration:
                pattern: Union[BugfixMetadata, None] = None
                while pattern is None:
                    try:
                        pattern = next(self.matching_patterns)
                    except StopIteration:
                        try:
                            self.candidate = self.get_bug_candidate()
                        except StopIteration:
                            raise StopIteration(
                                'No more bug candidates to abstract. Automatic Program Repair Failed!'
                                )
                        else:
                            self.abduction_depth = 0
                            self.abduction_breadth += 1
                            model = self.get_current_model()
                            logical_loc = self.LogicalLOC(self.candidate, ''.join(model))
                            
                            ast_bug_candidate = deepcopy(logical_loc.ast_node)
                            ast_hexdigest = self.abstract_bug_candidate(ast_bug_candidate)
                            
                            ast_bug_candidate = deepcopy(logical_loc.ast_node)
                            available_identifiers = logical_loc.get_available_identifiers()
                            patterns = self.get_matching_patterns(ast_hexdigest)
                            (self.matching_patterns, count) = patterns
                            logger.info(f"Current Candidate: {self.candidate}. Patterns Found: {count}")
                
                model = self.get_current_model()
                logical_loc = self.LogicalLOC(self.candidate, ''.join(model))
                ast_bug_candidate = deepcopy(logical_loc.ast_node)
                available_identifiers = logical_loc.get_available_identifiers()
                self.hypotheses_set = self.apply_bugfix_pattern(ast_bug_candidate, pattern, available_identifiers)
        self.build_hypothesis_model(hypothesis)
        self.abduction_breadth += 1

        return ('model1.py', hypothesis)

    def __enter__(self):
        return self

    def __exit__(self, exc_tp: Type, exc_value: BaseException,
                 exc_traceback: TracebackType) -> Optional[bool]:
        logger.info(f"\n<=== Exit Process Data ===>")
        logger.info(f"Current Candidate: {self.candidate}")
        logger.info(f"Remaining Candidates: {list(self.bug_candidates)}")
        logger.info(f"Abduction Depth: {self.abduction_depth}")
        logger.info(f"Abduction Breadth: {self.abduction_breadth}")
        logger.info(f"Abduction Complexity: {self.complexity}")
        logger.info(f"Total Number of Abductions Performed: {self.abduction_depth*self.complexity}")
        if exc_tp is not None:
            logger.warning("An error ocurred during the test.")
            logger.warning(f"{exc_tp}: {exc_value}")
            logger.warning(f"Unable to continue the test of hypothesis model: {self.model_name}")
        return True  # Ignore exception, if any

    def get_current_model(self):
        curr_dir = Path(__file__).parent.parent.resolve()
        curr_model_path = curr_dir.joinpath('temp', self.model_name)
        try:
            with open(curr_model_path, 'r') as f:
                model_src = f.readlines()
        except Exception as e:
            logger.exception(f"Unable to open the file: {self.model_name}.")
            return False
        return model_src

    @property
    def model_name(self):
        return f"model{str(self.abduction_depth)}.py"

    @staticmethod
    def mongodb_connection():
        config = DebugController.DATABASE_SETTINGS
        MONGO_URI = f"{config['URI']}://{config['HOST']}:{config['PORT']}"
        client = pymongo.MongoClient(MONGO_URI)
        db_connection = client[config['DATABASE']]
        #collection_BugPatterns = db_connection[config['COLLECTION']]
        return db_connection

