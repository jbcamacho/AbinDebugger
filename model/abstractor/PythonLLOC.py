"""
This module contains the support class PythonLLOC.
This class is used to obtain a Python Logical Line of Code (PythonLLOC).
"""
import tokenize
from io import BytesIO
import re
import ast
from typing import Tuple, Union
from model.abstractor.NodeMapper import NodeMapper, IDTokens, ASTNode

LogicalLOC = Union[Tuple[str, int, int], Tuple[None, int, int]]

class PythonLLOC(NodeMapper):
  """ This class acts as a support class to obtain
  a Python Logical Line of Code (PythonLLOC). """
  
  id_tokens: Union[None, IDTokens]
  line_no: int
  source_code: str
  def __init__(self, line_num: int, src: str) -> None:
      """Constructor Method"""
      self.line_no = line_num
      self.source_code = src
      self.id_tokens = None

  @property
  def logical_LOC(self) -> LogicalLOC:
    """ This property represents a logical line of Python code.

    :returns: A tuple representing the logical line of Python code, 
    if not found then an empty string will be returned.
    :rtype: LogicalLOC
    """
    curr_LOC: str = ''
    curr_LOC_start: int = 0
    found_LOC = False
    first_token = True
    src_utf8 = self.source_code.encode('utf-8')
    bytes_io = BytesIO(src_utf8).readline
    tokens = tokenize.tokenize(bytes_io)

    for etype, string, start, end, _ in tokens:
      token_line_start = start[0]
      token_line_end = end[0]
      # Check if the first token at self.lineno is a comment, if so,
      # return None as the given self.lineno corresponds to a comment
      if first_token and token_line_start == self.line_no:
        first_token = False
        if etype == tokenize.COMMENT:
          return (None, curr_LOC_start, token_line_end)

      if token_line_start <= self.line_no <= token_line_end:
        found_LOC = True
      
      if etype == tokenize.NEWLINE:
        if found_LOC:
          break
        curr_LOC = ''
        curr_LOC_start = token_line_start + 1
        continue

      # The process will skip comments, docstrings, encoding and non-terminating newlines.
      if (etype == tokenize.COMMENT or etype == tokenize.STRING or
          etype == tokenize.ENCODING or etype == tokenize.NL):
        continue
      curr_LOC += string + ' '
    if re.search('\S', curr_LOC):
      return (curr_LOC, curr_LOC_start, token_line_end)
    else:
      return (None, curr_LOC_start, token_line_end)

  @property
  def ast_node(self) -> Union[ASTNode, None]:
    """ This property represents the ASTNode corresponding to the given LOC.

    :returns: The AST Node representing the given logical LOC, 
        if not found then a None value will be returned.
    :rtype: ast.AST
    """
    try:
      logical_LOC = self.logical_LOC
    except Exception as e:
      print(f"An exception ocurred during the parsing.")
      print(f"Unable to parse the LOC at line no. {self.line_no}.")
      print(f"<--Exception Message-->\n\t{e}\n<--Exception Message-->")
      return None
    else:
      LOC = logical_LOC[0]
      line_start = logical_LOC[1]
      line_end = logical_LOC[2]
    if LOC == None:
      return None
    try:
      tree = ast.parse(self.source_code, mode='exec')
    except Exception as e:
      print(f"An exception ocurred during the parsing.")
      print(f"Unable to parse the LOC: {logical_LOC}")
      print(f"<--Exception Message-->\n\t{e}\n<--Exception Message-->")
      return None
    for node in ast.walk(tree):
      if hasattr(node, 'lineno'):
        if line_start <= node.lineno <= line_end:
          return node
    return None

  def get_nested_node(self) -> Union[str, None]:
    """ This method returns the a nested node name.

    If the Logical LOC is part of a elif-structure
    then the string 'elif' will be returned.
    
    :rtype: Union[str, None]
    """
    loc = None
    try:
      logical_LOC = self.logical_LOC
    except Exception as e:
      print(f"An exception ocurred during the parsing.")
      print(f"Unable to parse the LOC at line no. {self.line_no}.")
      print(f"<--Exception Message-->\n\t{e}\n<--Exception Message-->")
      return None
    
    loc = logical_LOC[0]
    if re.search('elif.*', loc):
      return 'elif'
    return None

  def get_available_identifiers(self) -> IDTokens:
    """ This method returns all the identifiers in an ASTNode.
        
    :rtype: IDTokens
    """
    try:
      ast_tree: ASTNode = ast.parse(self.source_code, mode='exec')
    except Exception as e:
      print(f"Unable to get the available identifiers.\nError: {e}")
    else:
      super().__init__(ast_tree)
      return self.id_tokens
    return {}
