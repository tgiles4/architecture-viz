from __future__ import annotations

import os
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from analyzer.fs_scan import scan_repository
from analyzer.ast_parse import parse_python_module
from analyzer.model import (
    AnalyzeResult,
    DependencyEdge,
    ModuleFacts,
    RepoFacts,
    PackageFacts,
)
from analyzer.summarize import summarize_repo


app = FastAPI(title="Architecture Viz Analyzer")


class AnalyzeRequest(BaseModel):
	root_path: str


@app.post("/analyze", response_model=AnalyzeResult)
def analyze(req: AnalyzeRequest) -> AnalyzeResult:
	root = os.path.abspath(req.root_path)
	if not os.path.isdir(root):
		raise HTTPException(status_code=400, detail=f"Invalid root_path: {root}")

	files = scan_repository(root)
	modules: List[ModuleFacts] = []
	module_by_name: Dict[str, ModuleFacts] = {}

	for f in files:
		if f.language == "python" and f.module:
			try:
				with open(f.path, "r", encoding="utf-8") as fh:
					text = fh.read()
				facts = parse_python_module(f.module, f.path, text)
				modules.append(facts)
				module_by_name[facts.module] = facts
			except Exception as e:  # pragma: no cover
				# Be robust; skip unreadable/invalid python files
				continue

	# Build simple dependency edges from imports
	edges: List[DependencyEdge] = []
	for m in modules:
		for imp in m.imports:
			if imp in module_by_name:
				edges.append(DependencyEdge(from_module=m.module, to_module=imp))

	# Group packages
    packages: Dict[str, List[ModuleFacts]] = {}
	for m in modules:
		pkg = m.module.rsplit(".", 1)[0] if "." in m.module else ""
		packages.setdefault(pkg, []).append(m)

    packages_facts: Dict[str, PackageFacts] = {
        pkg: PackageFacts(package=pkg, modules=mods) for pkg, mods in packages.items()
    }

    repo_facts = RepoFacts(
		root=root,
		files=files,
		modules=modules,
        packages=packages_facts,
		dependencies=edges,
	)

	summaries = summarize_repo(repo_facts)
	return AnalyzeResult(facts=repo_facts, summaries=summaries)


def create_app() -> FastAPI:
	return app


