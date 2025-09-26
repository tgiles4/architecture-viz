from __future__ import annotations

import ast
from typing import Dict, List, Set, Tuple, Optional

from .model import ModuleFacts


class CallNode:
    """Represents a function or method in the call graph."""
    def __init__(self, name: str, module: str, line: int, node_type: str = "function"):
        self.name = name
        self.module = module
        self.line = line
        self.node_type = node_type  # "function", "method", "class"
        self.calls: List[str] = []  # Functions this calls
        self.called_by: List[str] = []  # Functions that call this


class CallGraph:
    """Represents the call graph for a module or entire codebase."""
    def __init__(self):
        self.nodes: Dict[str, CallNode] = {}
        self.edges: List[Tuple[str, str]] = []  # (caller, callee)
    
    def add_node(self, node: CallNode):
        """Add a node to the call graph."""
        self.nodes[node.name] = node
    
    def add_edge(self, caller: str, callee: str):
        """Add an edge from caller to callee."""
        if caller in self.nodes and callee in self.nodes:
            self.nodes[caller].calls.append(callee)
            self.nodes[callee].called_by.append(caller)
            self.edges.append((caller, callee))
    
    def get_reachable_from(self, start_node: str, max_depth: int = 5) -> Dict[str, int]:
        """Get all nodes reachable from start_node with their depths."""
        if start_node not in self.nodes:
            return {}
        
        visited = {}
        queue = [(start_node, 0)]
        
        while queue and len(visited) < 100:  # Limit to prevent infinite loops
            current, depth = queue.pop(0)
            
            if current in visited:
                continue
                
            if depth > max_depth:
                continue
                
            visited[current] = depth
            
            # Add all functions called by current node
            if current in self.nodes:
                for callee in self.nodes[current].calls:
                    if callee not in visited:
                        queue.append((callee, depth + 1))
        
        return visited
    
    def get_paths_between(self, start: str, end: str, max_depth: int = 5) -> List[List[str]]:
        """Find all paths between start and end nodes."""
        if start not in self.nodes or end not in self.nodes:
            return []
        
        paths = []
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
                
            if current == end:
                paths.append(path)
                continue
            
            if current in self.nodes:
                for callee in self.nodes[current].calls:
                    if callee not in path:  # Avoid cycles
                        queue.append((callee, path + [callee]))
        
        return paths


def extract_call_relations(module_facts: ModuleFacts, source_code: str) -> CallGraph:
    """Extract call relations from a module's AST and source code."""
    callgraph = CallGraph()
    
    try:
        tree = ast.parse(source_code, filename=module_facts.path)
        
        # First pass: collect all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                call_node = CallNode(
                    name=node.name,
                    module=module_facts.module,
                    line=node.lineno,
                    node_type="function"
                )
                callgraph.add_node(call_node)
            elif isinstance(node, ast.ClassDef):
                # Add class as a node
                class_node = CallNode(
                    name=node.name,
                    module=module_facts.module,
                    line=node.lineno,
                    node_type="class"
                )
                callgraph.add_node(class_node)
                
                # Add methods as nodes
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        method_node = CallNode(
                            name=f"{node.name}.{method.name}",
                            module=module_facts.module,
                            line=method.lineno,
                            node_type="method"
                        )
                        callgraph.add_node(method_node)
        
        # Second pass: find function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Get the function being called
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # Handle method calls like obj.method()
                    callee_name = node.func.attr
                else:
                    continue
                
                # Find the function this call is in
                current_function = None
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.FunctionDef):
                        if (hasattr(node, 'lineno') and hasattr(parent, 'lineno') and 
                            parent.lineno <= node.lineno <= parent.end_lineno):
                            current_function = parent.name
                            break
                
                if current_function and callee_name in callgraph.nodes:
                    callgraph.add_edge(current_function, callee_name)
    
    except Exception:
        # If parsing fails, return empty call graph
        pass
    
    return callgraph


def build_module_callgraph(modules: List[ModuleFacts], file_contents: Dict[str, str]) -> CallGraph:
    """Build call graph for multiple modules."""
    global_callgraph = CallGraph()
    
    for module in modules:
        if module.path in file_contents:
            module_callgraph = extract_call_relations(module, file_contents[module.path])
            
            # Merge into global call graph
            for node in module_callgraph.nodes.values():
                global_callgraph.add_node(node)
            
            for caller, callee in module_callgraph.edges:
                global_callgraph.add_edge(caller, callee)
    
    return global_callgraph
