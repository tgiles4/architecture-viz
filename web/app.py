from __future__ import annotations

import os
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from analyzer.fs_scan import scan_repository
from analyzer.ast_parse import parse_python_module
from analyzer.model import DependencyEdge, ModuleFacts, PackageFacts, RepoFacts
from analyzer.callgraph import build_module_callgraph, CallGraph

app = FastAPI(title="Architecture Viz Web Interface")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Global cache for file contents and analysis results
file_cache: Dict[str, str] = {}
analysis_cache: Dict[str, dict] = {}
callgraph_cache: Dict[str, CallGraph] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with diagram interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/facts")
async def get_facts(request: dict) -> dict:
    """Return graph data for visualization."""
    root_path = request.get("root_path", "")
    if not root_path or not os.path.isdir(root_path):
        return {"error": "Invalid root path"}
    
    # Use existing analyzer logic
    files = scan_repository(root_path)
    modules = []
    module_by_name = {}
    
    for f in files:
        if f.language == "python" and f.module:
            try:
                with open(f.path, "r", encoding="utf-8") as fh:
                    text = fh.read()
                mf = parse_python_module(f.module, f.path, text)
                modules.append(mf)
                module_by_name[mf.module] = mf
            except Exception:
                continue
    
    # Build nodes and edges for D3
    nodes = []
    edges = []
    
    # Add module nodes
    for m in modules:
        nodes.append({
            "id": m.module,
            "type": "module",
            "name": m.module.split(".")[-1],
            "full_name": m.module,
            "classes": len(m.classes),
            "functions": len(m.functions),
            "imports": len(m.imports)
        })
    
    # Add package nodes
    packages = {}
    for m in modules:
        pkg = m.module.rsplit(".", 1)[0] if "." in m.module else ""
        if pkg:
            packages.setdefault(pkg, []).append(m)
    
    for pkg_name, pkg_modules in packages.items():
        if pkg_name:  # Skip empty package names
            nodes.append({
                "id": f"pkg_{pkg_name}",
                "type": "package",
                "name": pkg_name.split(".")[-1],
                "full_name": pkg_name,
                "modules": len(pkg_modules)
            })
    
    # Add edges
    for m in modules:
        for imp in m.imports:
            if imp in module_by_name:
                edges.append({
                    "source": m.module,
                    "target": imp,
                    "type": "import"
                })
    
    # Add package-to-module edges
    for pkg_name, pkg_modules in packages.items():
        if pkg_name:
            for m in pkg_modules:
                edges.append({
                    "source": f"pkg_{pkg_name}",
                    "target": m.module,
                    "type": "contains"
                })
    
    # Cache file contents and analysis results
    cache_key = f"{root_path}_{len(files)}"
    for f in files:
        if f.language == "python" and f.module:
            try:
                with open(f.path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                    file_cache[f.path] = content
            except Exception:
                continue
    
    analysis_cache[cache_key] = {
        "files": files,
        "modules": modules,
        "packages": packages
    }
    
    # Build call graph and cache it
    callgraph = build_module_callgraph(modules, file_cache)
    callgraph_cache[cache_key] = callgraph
    
    return {
        "nodes": nodes,
        "edges": edges,
        "files": files,  # Include files array for source lookup
        "stats": {
            "total_files": len(files),
            "python_files": len([f for f in files if f.language == "python"]),
            "modules": len(modules),
            "packages": len(packages)
        }
    }


@app.get("/source")
async def get_source(path: str, symbol: Optional[str] = None) -> dict:
    """Get source code snippet for a file and optional symbol."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get file content from cache or read from disk
    if path in file_cache:
        content = file_cache[path]
    else:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
                file_cache[path] = content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot read file: {e}")
    
    lines = content.split('\n')
    
    # If symbol is specified, try to find it in the content
    if symbol:
        symbol_lines = []
        in_symbol = False
        indent_level = None
        
        for i, line in enumerate(lines):
            # Look for function or class definition
            if symbol in line and ('def ' in line or 'class ' in line):
                in_symbol = True
                indent_level = len(line) - len(line.lstrip())
                symbol_lines.append((i + 1, line))
            elif in_symbol:
                if line.strip() == '':
                    symbol_lines.append((i + 1, line))
                elif len(line) - len(line.lstrip()) > indent_level:
                    symbol_lines.append((i + 1, line))
                else:
                    break
        
        if symbol_lines:
            start_line = symbol_lines[0][0]
            end_line = symbol_lines[-1][0]
            symbol_content = '\n'.join([line for _, line in symbol_lines])
        else:
            # Fallback: return lines containing the symbol
            matching_lines = []
            for i, line in enumerate(lines):
                if symbol in line:
                    matching_lines.append((i + 1, line))
            if matching_lines:
                start_line = matching_lines[0][0]
                end_line = matching_lines[-1][0]
                symbol_content = '\n'.join([line for _, line in matching_lines])
            else:
                start_line = 1
                end_line = min(10, len(lines))
                symbol_content = '\n'.join(lines[:end_line])
    else:
        # Return first 50 lines if no symbol specified
        start_line = 1
        end_line = min(50, len(lines))
        symbol_content = '\n'.join(lines[:end_line])
    
    return {
        "path": path,
        "symbol": symbol,
        "content": symbol_content,
        "start_line": start_line,
        "end_line": end_line,
        "total_lines": len(lines),
        "language": "python" if path.endswith('.py') else "text"
    }


@app.get("/callgraph")
async def get_callgraph(symbol: str, root_path: str, max_depth: int = 5, include_external: bool = False) -> dict:
    """Get call graph starting from a specific symbol."""
    # Find the matching cache key
    cache_key = None
    for key in callgraph_cache.keys():
        if key.startswith(root_path):
            cache_key = key
            break
    
    if not cache_key or cache_key not in callgraph_cache:
        raise HTTPException(status_code=404, detail="Analysis not found. Please run analysis first.")
    
    callgraph = callgraph_cache[cache_key]
    
    # Get reachable nodes from the symbol
    reachable = callgraph.get_reachable_from(symbol, max_depth)
    
    # Build nodes and edges for visualization
    nodes = []
    edges = []
    
    # Add the starting node
    if symbol in callgraph.nodes:
        start_node = callgraph.nodes[symbol]
        nodes.append({
            "id": symbol,
            "name": symbol,
            "type": start_node.node_type,
            "module": start_node.module,
            "line": start_node.line,
            "depth": 0
        })
    
    # Add reachable nodes
    for node_name, depth in reachable.items():
        if node_name != symbol and node_name in callgraph.nodes:
            node = callgraph.nodes[node_name]
            nodes.append({
                "id": node_name,
                "name": node_name,
                "type": node.node_type,
                "module": node.module,
                "line": node.line,
                "depth": depth
            })
    
    # Add edges between reachable nodes
    for caller, callee in callgraph.edges:
        if caller in reachable and callee in reachable:
            edges.append({
                "source": caller,
                "target": callee,
                "type": "call"
            })
    
    return {
        "symbol": symbol,
        "nodes": nodes,
        "edges": edges,
        "max_depth": max_depth,
        "total_reachable": len(reachable)
    }


@app.get("/callgraph/paths")
async def get_callgraph_paths(start: str, end: str, root_path: str, max_depth: int = 5) -> dict:
    """Get paths between two symbols."""
    # Find the matching cache key
    cache_key = None
    for key in callgraph_cache.keys():
        if key.startswith(root_path):
            cache_key = key
            break
    
    if not cache_key or cache_key not in callgraph_cache:
        raise HTTPException(status_code=404, detail="Analysis not found. Please run analysis first.")
    
    callgraph = callgraph_cache[cache_key]
    paths = callgraph.get_paths_between(start, end, max_depth)
    
    return {
        "start": start,
        "end": end,
        "paths": paths,
        "path_count": len(paths),
        "max_depth": max_depth
    }


def create_app() -> FastAPI:
    return app
