import ast
import json
import copy
from typing_extensions import TypedDict
from model.abstractor.NodeMapper import NodeMapper, ASTNode, IDTokens
from model.abstractor.PythonLLOC import PythonLLOC, LogicalLOC
from model.abstractor.NodeAbstractor import NodeAbstractor, NodeMetadata

class BugfixMetadata(TypedDict):
    """ This class defines the JSON structure of
    the bugfix's metadata"""
    commit_sha: str
    available_identifiers: IDTokens
    bug_metadata: NodeMetadata
    fix_metadata: NodeMetadata

class Bugfix():
  """ This class represent a bugfix obtained from a bugfixing commit"""
  bugged_LOC: LogicalLOC
  fixed_LOC: LogicalLOC
  bugged_node: ASTNode
  fixed_node: ASTNode
  bug: NodeAbstractor
  fix: NodeAbstractor
  _notes: str

  def __init__( self, 
    bugged_lineno: int, bugged_source: str, 
    fixed_lineno: int, fixed_source: str ) -> None:
    """ Constructor method """
    self.bugged_LOC = PythonLLOC(bugged_lineno, bugged_source)
    self._notes = ""
    bugged_node = copy.deepcopy(self.bugged_LOC.ast_node)
    nodes_mapping = ({}, {})
    if bugged_node == None:
      self.bug = None
    else:
      self.bug = NodeAbstractor(bugged_node)
      nodes_mapping = (self.bug.map_ids.copy(), self.bug.map_nodes.copy())
  
    self.fixed_LOC = PythonLLOC(fixed_lineno, fixed_source)
    fixed_node = copy.deepcopy(self.fixed_LOC.ast_node)
    if fixed_node == None:
      self.fix = None
    else:
      self.fix = NodeAbstractor(fixed_node, nodes_mapping)

  def __str__(self):
    """ Class String representation method """
    print_data = json.dumps(self.bugfix_data, indent=4)
    return self._notes + f'\nMetadata: {print_data}'

  @property
  def bugfix_data(self) -> BugfixMetadata:
    """ This property returns the bugfix's metadata.

      :rtype: BugfixMetadata
      """
    bugfix_metadata: BugfixMetadata = {}
    if self.bug and self.fix:
      bug_metadata = self.bug.ast_node_data
      fix_metadata = self.fix.ast_node_data
      bug_sha = bug_metadata.get('hexdigest')
      fix_sha = fix_metadata.get('hexdigest')
      if bug_sha != fix_sha:
        bug_metadata.update({ "LOC" : self.bugged_LOC.logical_LOC })
        fix_metadata.update({ "LOC" : self.fixed_LOC.logical_LOC  }) 

        bugfix_metadata = {
            "commit_sha": "",
            "available_identifiers": self.get_available_identifiers(),
            "bug_metadata": bug_metadata.copy(),
            "fix_metadata": fix_metadata.copy()
        }
        self._notes = 'Correct Bugfix.'
      else:
        self._notes = f'Equal Fix and Bug.\
        \nBUG:{self.bugged_LOC.logical_LOC} \
        \nFIX:{self.fixed_LOC.logical_LOC} \
        \nThe bugfix\'s metadata will be Empty.'
    else:
      self._notes = 'One or both nodes\' metadata is empty. \
      The bugfix\'s metadata will be Empty.'
    return bugfix_metadata

  def get_bug_node(self) -> ASTNode:
    """ This method return the ASTNode object corresponding to the bug
    
    : rtype: ASTNode
    """
    data = self.bug.ast_node_data
    node = eval(data['abstract_node'], vars(ast), {})
    return node

  def get_fix_node(self) -> ASTNode:
    """ This method return the ASTNode object corresponding to the fix 
    
    : rtype: ASTNode
    """
    data = self.fix.ast_node_data
    node = eval(data['abstract_node'], vars(ast), {})
    return node
  
  def get_available_identifiers(self) -> IDTokens:
    """ This method return all the available identifiers
    
    This method uses two instances of `NodeMapper`,
    in order to obtain both (bug and fix) identifiers
    and merge them together.
    
    : rtype: IDTokens
    """
    tree_bug = self.bugged_LOC.ast_node
    bug_mapper = NodeMapper(tree_bug, prepare_node=True)
    tree_fix = self.fixed_LOC.ast_node
    fix_mapper = NodeMapper(tree_fix, prepare_node=True)

    all_keys = set(bug_mapper.id_tokens.keys()).union(set(fix_mapper.id_tokens.keys()))
    identifiers: IDTokens = {key:set() for key in all_keys}
    for id in identifiers:
      set1 = bug_mapper.id_tokens.get(id, set())
      set2 = fix_mapper.id_tokens.get(id, set())
      identifiers[id] = list(set1.union(set2))
    return identifiers