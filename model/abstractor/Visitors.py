import ast
from astunparse import unparse
from copy import deepcopy
from typing import List, Dict

class RecursiveVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def recursive(func):
        """ decorator to make visitor work recursive """
        def wrapper(self,node):
            func(self,node)
            for child in ast.iter_child_nodes(node):
                self.visit(child)
        return wrapper

class GenericVisitor(RecursiveVisitor):
    @RecursiveVisitor.recursive
    def generic_visit(self, node: ast.AST):
        pass

class TargetVisitor(GenericVisitor):
    def __init__(self, target: str, ast_tree: ast.AST) -> None:
        super().__init__()
        self.target_func = target
        self.target_node = None
        self.func_names = set()
        self.visit(ast_tree)

    @GenericVisitor.recursive
    def visit_FunctionDef(self, node: ast.AST):
        self.func_names.add(node.name)
        if node.name == self.target_func:
          self.target_node = node       

class FunctionVisitor(GenericVisitor):
    def __init__(self, func_names: List[str], ast_tree: ast.AST) -> None:
        super().__init__()
        self.func_names = func_names
        self.func_nodes = set()
        self.visit(ast_tree)
    
    @GenericVisitor.recursive
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in self.func_names:
          self.func_nodes.add(node)

class CallVisitor(GenericVisitor):
    def __init__(self, func_names: List[str], ast_tree: ast.AST) -> None:
        super().__init__()
        self.func_names = func_names
        self.call_names = set()
        self.visit(ast_tree)

    @GenericVisitor.recursive
    def visit_Call(self, node: ast.Call) -> None:
        if node.func.id in self.func_names:
          self.call_names.add(node.func.id)

class StatementVisitor(GenericVisitor):
    def __init__(self, rank: Dict, ast_tree: ast.AST) -> None:
        super().__init__()
        self.statements = set()
        self.rank = rank
        self.visit(ast_tree)

    @GenericVisitor.recursive
    def generic_visit(self, node: ast.AST):
        node_type = node.__class__.__name__
        if isinstance(node, ast.stmt) and node_type in self.rank.keys():
          support_node = deepcopy(node)
          if hasattr(node, 'body'): support_node.body = []
          if hasattr(node, 'orelse'): support_node.orelse = []
          if hasattr(node, 'finalbody'): support_node.finalbody = []
          _stmt = (node.lineno, unparse(support_node), self.rank[node_type])
          self.statements.add(_stmt)