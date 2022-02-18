import ast
import builtins 
from typing import Type, Callable, List, Union, Any, Dict, Set, AnyStr

ASTIdentifier = AnyStr
ASTIdentifiers = List[ASTIdentifier]
IDToken = AnyStr
IDTokens = Dict[str, Set[IDToken]]
ASTNode = Type[ast.AST]

class RecursiveVisitor(ast.NodeVisitor):
    """ 
    This class is used to visit all the nodes in a ast and get the avaiable identifiers 
    """
    ast_identifiers: ASTIdentifiers
    id_tokens: IDTokens

    def __init__(self, ast_node: ASTNode, prepare_node: bool = False) -> None:
      self.ast_identifiers: ASTIdentifiers = ['id', 'n', 's', 'name', 'asname', 'module', 'attr', 'arg']
      self.id_tokens = {}
      if prepare_node:
        self.visit(self.prepare_node(ast_node))
      else:
        self.visit(ast_node)

    def recursive(func: Callable) -> Callable:
        """ decorator to make visitor work recursive """
        def wrapper(self, node: ASTNode) -> None:
            func(self, node)
            for child in ast.iter_child_nodes(node):
                self.visit(child)
        return wrapper
    
    @recursive
    def generic_visit(self, node: ASTNode) -> None:
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
      return True if (obj_name in dir(builtins)) else False

    @staticmethod
    def prepare_node(node: ASTNode) -> ASTNode:
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