"""
This module contains the NodeMapper class
that works as a support class to obtain
all the identifiers in a given AST.
"""
import ast
import builtins 
from typing import List, Union, Any, Dict, Set
from model.abstractor.Visitors import RecursiveVisitor

ASTIdentifier = str
ASTIdentifiers = List[ASTIdentifier]
IDToken = str
IDTokens = Dict[str, Set[IDToken]]
ASTNode = ast.AST

class NodeMapper(RecursiveVisitor):
    """ This class is used to visit all the nodes in a ast.AST
    and get the avaiable identifiers."""

    ast_identifiers: ASTIdentifiers
    id_tokens: IDTokens
    def __init__(self, ast_node: ASTNode, prepare_node: bool = False) -> None:
      """ Constructor Method """
      super().__init__()
      self.ast_identifiers: ASTIdentifiers = ['id', 'n', 's', 'name', 'asname', 'module', 'attr', 'arg']
      self.id_tokens = {}
      if prepare_node:
        self.visit(self.prepare_node(ast_node))
      else:
        self.visit(ast_node)
    
    @RecursiveVisitor.recursive
    def generic_visit(self, node: ASTNode) -> None:
        """ Method to visit all the nodes.

        If the visited node have an identifier,
        it will be mapped to the self.id_tokens.
        
        :param node: The visited node
        :type  node: ASTNode
        :rtype: None
        """
        node_name: str
        node_id: Union[Any, None]
        for ast_id in self.ast_identifiers:
          if hasattr(node, ast_id):
            node_name = node.__class__.__name__
            node_id = getattr(node, ast_id, None)
            node_id = str(node_id)
            if self.is_builtins(node_id):
              if 'Built-in' in self.id_tokens.keys():
                self.id_tokens['Built-in'].add(node_id)
              else:
                self.id_tokens['Built-in'] = set()
                self.id_tokens['Built-in'].add(node_id)
            elif node_name in self.id_tokens.keys():
              self.id_tokens[node_name].add(node_id)
            else:
              self.id_tokens[node_name] = set()
              self.id_tokens[node_name].add(node_id)
    
    @staticmethod
    def is_builtins(obj_name: str) -> bool:
      """ Method to query membership of an object to builtins.
      
      :param obj_name: The object name
      :type  obj_name: str
      :rtype: bool
      """
      return True if (obj_name in dir(builtins)) else False

    @staticmethod
    def prepare_node(node: ASTNode) -> ASTNode:
      """ Method to prepare an ASTNode.

      This method removes the node body, orelse, finalbody properties.
      
      :param node: The visited node
        :type  node: ASTNode
        :rtype: ASTNode
      """
      if hasattr(node, 'body'):
        if node.body != []:
          node.body = []
      if hasattr(node, 'orelse'):
        if node.orelse != []:
          node.orelse = []
      if hasattr(node, 'finalbody'):
        if node.finalbody != []:
          node.finalbody = []
      return node