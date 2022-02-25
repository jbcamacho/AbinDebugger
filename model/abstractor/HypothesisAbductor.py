"""
This module contains the core class HypothesisAbductor.
This class is used to abduct a hypotheses.
"""
import ast
import astunparse
import re
import copy
import itertools
from typing import Union, Type, Tuple, List
from model.abstractor.Bugfix import BugfixMetadata
from model.abstractor.NodeAbstractor import IDMapping, NodeAbstractor, NodeMapping
from model.abstractor.NodeMapper import ASTIdentifiers, ASTNode, IDTokens


class HypothesisAbductor(ast.NodeVisitor):
  """ This is the core class used to abduct a new hypothesis """
  ast_identifiers: ASTIdentifiers
  abducted_fix: Union[None, NodeAbstractor]
  actual_bug: Union[None, NodeAbstractor]
  bugfix: BugfixMetadata
  posible_ids: Type[itertools.product]
  map_tuple_ordering: List

  def __init__(self,
        node_to_abduct: ASTNode,
        bugfix: BugfixMetadata,
        available_identifiers: IDTokens = []) -> None:
    """ Constructor method """
    self.abducted_fix = None
    self.ast_identifiers = ['id', 'n', 's', 'name', 'asname', 'module', 'attr', 'arg']
    self.available_identifiers = self.merge_available_identifiers(
                                          available_identifiers, 
                                          bugfix['available_identifiers'])
    if node_to_abduct is None:
      self.actual_bug = None
    else:
      actual_bug = copy.deepcopy(node_to_abduct)
      self.actual_bug = NodeAbstractor(actual_bug)
    self.bugfix = bugfix
    (ids, ordering) = self.get_possible_ids()
    self.posible_ids = ids
    self.map_tuple_ordering = ordering
    
  def abduct_fix(self) -> None:
    """ This method controls the abduction process. """
    (new_mapping_id, new_mapping_nodes) = self.next_abductive_mapping()
    self.abducted_fix = eval(self.bugfix['fix_metadata']['abstract_node'], vars(ast), {})
    self.abducted_fix.map_ids = new_mapping_id.copy()
    self.abducted_fix.map_nodes = new_mapping_nodes.copy()
    self.visit(self.abducted_fix)

  def abduct_node(self, node: ASTNode) -> None:
    """ This method tranforms the given node in a hypothesis
    
    This method will transverse all the abstracted identifiers
    and replace them by a new node mappping, in order to,
    get a whole new hypothesis.

    :param node: The abstracted node
    :type  node: ASTNode
    :rtype: None
    """
    for ast_id in self.ast_identifiers:
      if hasattr(node, ast_id):
        node_id = getattr(node, ast_id, None)
        node_id = str(node_id)
        if node_id in self.abducted_fix.map_ids:
          abduction = self.abducted_fix.map_ids[node_id]
          node_type = re.sub('\d+$', '', node_id)
          if node_type == 'Num':
            if self.is_int(abduction):
              abduction = int(abduction)
            elif self.is_float(abduction):
              abduction = float(abduction)
            elif self.is_complex(abduction):
              abduction = complex(abduction)
          elif node_type == 'Bytes':
            abduction = bytes(abduction, 'utf-8')
          setattr(node, ast_id, abduction)

  def generic_visit(self, node: ASTNode) -> None:
    """ Method to visit all the nodes.

    The method `abduct_node` will be applied to all the visited nodes.
        
    :param node: The visited node
    :type  node: ASTNode
    :rtype: None
    """
    self.abduct_node(node)
    for child in ast.iter_child_nodes(node):
        self.visit(child)

  def diff_node_mapping(self) -> NodeMapping:
    """ This Method will calculate the difference between two NodeMappings.

    :rtype: NodeMapping
    """
    map_to_fix = self.bugfix['fix_metadata']['map_nodes']
    map_bug = self.actual_bug.map_nodes.copy()
    all_keys = set(map_to_fix.keys()).union(set(map_bug.keys()))
    map_result = {}
    for key in all_keys:
      if key in map_to_fix and key not in map_bug:
        map_result[key] = map_to_fix[key] + 1
      elif key in map_to_fix and key in map_bug:
        if map_to_fix[key] == map_bug[key]:
          continue
        map_result[key] = abs(map_to_fix[key] - map_bug[key])
    return map_result

  def get_possible_ids(self) -> Type[itertools.product]:
    """ This Method will calculate the product of the missing IDs.

    The product is a n-tuple of the missing identifiers requiered
    to fill the abstractions during the `abduct_node` process.

    :rtype: Type[itertools.product]
    """
    if self.actual_bug is None: return (iter([]), ())
    map_tuple = self.diff_node_mapping()
    n_tuple = []
    n_tuple_ordering = []
    for key, value in map_tuple.items():
      for i in range(value):
        n_tuple_ordering.append(key)
        n_tuple.append(self.available_identifiers[key])
    # The starred expression is used to unpack a iterable
    return (itertools.product(*n_tuple), n_tuple_ordering)

  def next_abductive_mapping(self) -> Tuple[IDMapping, NodeMapping]:
    """ This method generate a Tuple[IDMapping, NodeMapping].
    
    : rtype: Tuple[IDMapping, NodeMapping]
    """
    curr_ids = self.curr_ids
    map_ids_fix = {value:key for key, value in self.actual_bug.map_ids.copy().items()}
    map_nodes_fix = self.actual_bug.map_nodes.copy()
    for i, order in enumerate(self.map_tuple_ordering):
      if order in map_nodes_fix:
        map_nodes_fix[order] += 1
      else:
        map_nodes_fix[order] = 0
      abstraction = order + str(map_nodes_fix[order])
      node_id = curr_ids[i]
      map_ids_fix[abstraction] = node_id
    return (map_ids_fix, map_nodes_fix)

  @property
  def hypothesis(self) -> str:
    """ This property represents the abducted hypothesis """
    if self.abducted_fix:
      LOC = astunparse.unparse(self.abducted_fix)
      #just keep the unicode str of LOC
      LOC = re.sub('[\t\n\r\f\v]', '', LOC)
      return LOC
    return None

  def __iter__(self) -> None:
    """ Class Iterator Constructor """
    return self

  def __next__(self) -> str:
    """ Class Iterator Next Constructor

    This method will iterate over all posible hypothesis
    until the iterator `self.posible_ids` is exhausted.
    
    : rtype: str
    """
    try:
      self.curr_ids = list(next(self.posible_ids))
    except StopIteration:
      self.abducted_fix = None
      raise StopIteration
    else:
      self.abduct_fix()
      return self.hypothesis

  @staticmethod
  def merge_available_identifiers(id_tokens1: IDTokens, id_tokens2: IDTokens) -> IDTokens:
    """ This method merge two IDTokens into one.
    
    :param id_tokens1: The identifiers mapping 1
    :type  id_tokens1: IDTokens
    :param id_tokens2: The identifiers mapping 2
    :type  id_tokens2: IDTokens
    :rtype: IDTokens
    """
    all_keys = set(id_tokens1.keys()).union(set(id_tokens2.keys()))
    identifiers = {key:set() for key in all_keys}
    for id in identifiers:
      set1 = id_tokens1.get(id, set())
      set2 = id_tokens2.get(id, set())
      identifiers[id] = list(set1.union(set2))
    return identifiers

  @staticmethod
  def is_int(x):
    """ This method check if a given string is an integer type """
    try:
        a = int(x)
    except (TypeError, ValueError):
        return False
    else:
        return True

  @staticmethod
  def is_float(x):
    """ This method check if a given string is a float type """
    try:
        a = float(x)
    except (TypeError, ValueError):
        return False
    else:
        return True

  @staticmethod
  def is_complex(x):
    """ This method check if a given string is a complex type """
    try:
      a = complex(x)
    except (TypeError, ValueError):
      return False
    else:
      return True