"""
This module contains all the visitors class needed in the peoject.
"""
import ast
from astunparse import unparse
from copy import deepcopy
from typing import List, Dict, Any, Union, Set
from types import FunctionType

ASTNode = ast.AST
class RecursiveVisitor(ast.NodeVisitor):
    """Base class for all the AST node visitors"""
    def __init__(self) -> None:
        """Constructor Method"""
        super().__init__()

    @staticmethod
    def recursive(func: FunctionType) -> Any:
        """ Decorator to allow visitor methods to perform recursive calls.
        
        :param func: The visit function
        :type  func: FunctionType
        :rtype: Any
        """
        def wrapper(self, node: ASTNode):
            func(self,node)
            for child in ast.iter_child_nodes(node):
                self.visit(child)
        return wrapper

class GenericVisitor(RecursiveVisitor):
    """ Support class to recursively visit all nodes in a ASTNode"""
    @RecursiveVisitor.recursive
    def generic_visit(self, node: ASTNode) -> None:
        """ Method to recursively visit all the nodes.
        
        :param node: The visited node
        :type  node: ASTNode
        :rtype: None
        """
        pass

class TargetVisitor(GenericVisitor):
    """Class that saves a pointer to specific targeted function in a ast_tree"""
    target_func: str
    target_node: Union[None, ASTNode]
    func_names: Set[str]
    def __init__(self, target: str, ast_tree: ASTNode) -> None:
        """Constructor Method"""
        super().__init__()
        self.target_func = target
        self.target_node = None
        self.func_names = set()
        self.visit(ast_tree)

    @GenericVisitor.recursive
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """ Method to visit all the FunctionDef nodes in a ASTNode.

        This method will save a pointer to the node that
        the targeted function belongs to.
        
        :param node: The visited node
        :type  node: ast.FunctionDef
        :rtype: None
        """
        self.func_names.add(node.name)
        if node.name == self.target_func:
          self.target_node = node       

class FunctionVisitor(GenericVisitor):
    """Class that saves all the pointers to
    the ast.FunctionDef nodes in the ast_tree"""
    def __init__(self, func_names: List[str], ast_tree: ASTNode) -> None:
        """Constructor Method"""
        super().__init__()
        self.func_names = func_names
        self.func_nodes = set()
        self.visit(ast_tree)
    
    @GenericVisitor.recursive
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """ Method to visit all the FunctionDef nodes in a ASTNode.

        This method will save all the pointers to
        the FunctionDef nodes in the ast_tree.
        
        :param node: The visited node
        :type  node: ast.FunctionDef
        :rtype: None
        """
        if node.name in self.func_names:
          self.func_nodes.add(node)

class CallVisitor(GenericVisitor):
    """Class that saves all the identifiers that
    belongs to ast.Call nodes in the ast_tree"""
    def __init__(self, func_names: List[str], ast_tree: ASTNode) -> None:
        """Constructor Method"""
        super().__init__()
        self.func_names = func_names
        self.call_names = set()
        self.visit(ast_tree)

    @GenericVisitor.recursive
    def visit_Call(self, node: ast.Call) -> None:
        """ Method to visit all the Call nodes in a ASTNode.

        This method will save all the identifiers that
        belongs to Call nodes in the ast_tree.
        
        :param node: The visited node
        :type  node: ast.Call
        :rtype: None
        """
        if node.func.id in self.func_names:
          self.call_names.add(node.func.id)

class StatementVisitor(GenericVisitor):
    """Class that saves all the unparsed ast.stmt nodes in a ast_tree"""
    def __init__(self, rank: Dict, ast_tree: ASTNode) -> None:
        """Constructor Method"""
        super().__init__()
        self.statements = set()
        self.rank = rank
        self.visit(ast_tree)

    @GenericVisitor.recursive
    def generic_visit(self, node: ASTNode):
        """ Method to visit all the nodes.

        The visited node will be unparsed and saved,
        if the visited node is instance of ast.stmt
        and the node type is in the rank.
        
        :param node: The visited node
        :type  node: ASTNode
        :rtype: None
        """
        node_type = node.__class__.__name__
        if isinstance(node, ast.stmt) and node_type in self.rank.keys():
          support_node = deepcopy(node)
          if hasattr(node, 'body'): support_node.body = []
          if hasattr(node, 'orelse'): support_node.orelse = []
          if hasattr(node, 'finalbody'): support_node.finalbody = []
          _stmt = (node.lineno, unparse(support_node), self.rank[node_type])
          self.statements.add(_stmt)