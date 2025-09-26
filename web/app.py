from __future__ import annotations

import os
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from analyzer.fs_scan import scan_repository
from analyzer.ast_parse import parse_python_module
from analyzer.model import DependencyEdge, ModuleFacts, PackageFacts, RepoFacts

app = FastAPI(title="Architecture Viz Web Interface")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")


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
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_files": len(files),
            "python_files": len([f for f in files if f.language == "python"]),
            "modules": len(modules),
            "packages": len(packages)
        }
    }


def create_app() -> FastAPI:
    return app
