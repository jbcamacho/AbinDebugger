"""
This module contains the NodeAbstractor class
that is the core class to abract the ASTs.
"""
import ast
import hashlib
from typing import List, Union, Tuple, Type, Dict
from typing_extensions import TypedDict
from model.abstractor.NodeMapper import ASTIdentifiers, ASTNode, NodeMapper

UserIdentifier = str
NodeAbstraction = str
NodeName = Type[ast.AST.__name__]
IDMapping = Dict[UserIdentifier, NodeAbstraction]
NodeMapping = Dict[NodeName, int]

class NodeMetadata(TypedDict):
  """ This class defines the JSON structure of
  the abstracted node's metadata"""
  hexdigest: str
  ast_type: str
  abstract_node: str
  map_ids: IDMapping
  map_nodes: NodeMapping

class NodeAbstractor(NodeMapper):
    """ This class is used to abstract an AST node. """
    ast_identifiers: ASTIdentifiers
    ast_node: ASTNode
    map_ids: IDMapping
    map_nodes: NodeMapping
    adj_lst: List

    def __init__(self, node_to_abstract: ASTNode, 
                 nodes_mapping: Union[Tuple[IDMapping, NodeMapping], None] = None) -> None:
      """Constructor Method"""
      self.ast_identifiers = ['id', 'n', 's', 'name', 'asname', 'module', 'attr', 'arg']
      self.ast_node = self.prepare_node(node_to_abstract)
      self.adj_lst = {}
      if nodes_mapping == None:
        self.map_ids = {}
        self.map_nodes = {}
      else:
        (self.map_ids, self.map_nodes) = nodes_mapping
      
      self.visit(self.ast_node)

    
    def generic_visit(self, node: ASTNode) -> None:
      """ Method to visit to every node in the `node_to_abstract`.
      
      This function is called every time a new node is visited
      and assign a new attribute `abstraction` to the node.

      :param node: The AST Node.
      :type  node: ASTNode
      :rtype: None
      """
      node.abstraction = self.abstract_node(node)
      if node.abstraction not in self.adj_lst.keys():
        self.adj_lst[node.abstraction] = []
      for child in ast.iter_child_nodes(node):
        self.visit(child)
        if child.abstraction not in self.adj_lst[node.abstraction]:
          self.adj_lst[node.abstraction].append(child.abstraction)

    
    def abstract_node(self, node: ASTNode) -> NodeAbstraction:
      """ This method abstracts the given AST.
      
      The abstraction will be mappend into a NodeMapping
      and it will be returned.

      :param node: The AST Node.
      :type  node: ASTNode
      :rtype: str
      """
      abstraction: NodeAbstraction
      if hasattr(node, 'abstraction'):
        # Do not abstract a node that already has an abstraction
        return node.abstraction
      node_name = type(node).__name__
      abstraction = node_name
      for ast_id in self.ast_identifiers:
        if hasattr(node, ast_id):
          node_id = getattr(node, ast_id, None)
          node_id = str(node_id)
          if node_id not in self.map_ids:
            if self.is_builtins(node_id):
              node_name = 'Built-in'
              if 'Built-in' in self.map_nodes:
                self.map_nodes['Built-in'] += 1
              else:
                self.map_nodes['Built-in'] = 0
            elif node_name in self.map_nodes:
              self.map_nodes[node_name] += 1
            else:
              self.map_nodes[node_name]  = 0
            abstraction = node_name + str(self.map_nodes[node_name])
            self.map_ids[node_id] = abstraction
          else:
            abstraction = self.map_ids[node_id]
          setattr(node, ast_id, abstraction)
      return abstraction

    @property
    def ast_graph(self) -> str:
      """ This property returns the node ast graph as a JSON string.

      :rtype: str
      """
      return ast.dump(self.ast_node, annotate_fields=False)

    @property
    def ast_hexdigest(self) -> str:
      """ This property returns the hexdigest of the self.ast_graph property.

      :rtype: str
      """
      m = hashlib.sha256()
      data = self.ast_graph.encode('utf-8')
      m.update(data)
      return m.hexdigest()

    @property
    def ast_node_data(self) -> NodeMetadata:
      """ This property returns the abstracted node's metadata.

      :rtype: NodeMetadata
      """
      data: NodeMetadata
      if self.ast_node:
        data = {
            "hexdigest": self.ast_hexdigest,
            "ast_type": type(self.ast_node).__name__,
            "abstract_node": self.ast_graph,
            "map_ids": {value:key for key, value in self.map_ids.copy().items()},
            "map_nodes": self.map_nodes.copy()
        }
        return data
      return {}