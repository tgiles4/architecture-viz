from __future__ import annotations

import argparse
import json
import os

import uvicorn

from analyzer.fs_scan import scan_repository
from analyzer.ast_parse import parse_python_module
from analyzer.model import RepoFacts, DependencyEdge, PackageFacts
from analyzer.summarize import summarize_repo


def cmd_analyze(args: argparse.Namespace) -> None:
	root = os.path.abspath(args.path)
	files = scan_repository(root)
	modules = []
	module_by_name = {}
	for f in files:
		if f.language == "python" and f.module:
			with open(f.path, "r", encoding="utf-8") as fh:
				text = fh.read()
				mf = parse_python_module(f.module, f.path, text)
				modules.append(mf)
				module_by_name[mf.module] = mf

	edges = []
	for m in modules:
		for imp in m.imports:
			if imp in module_by_name:
				edges.append(DependencyEdge(from_module=m.module, to_module=imp))

	packages = {}
	for m in modules:
		pkg = m.module.rsplit(".", 1)[0] if "." in m.module else ""
		packages.setdefault(pkg, []).append(m)
	packages_facts = {pkg: PackageFacts(package=pkg, modules=mods) for pkg, mods in packages.items()}

	repo_facts = RepoFacts(root=root, files=files, modules=modules, packages=packages_facts, dependencies=edges)
	summaries = summarize_repo(repo_facts)
	print(json.dumps({"facts": repo_facts.model_dump(), "summaries": summaries.model_dump()}, indent=2))


def cmd_serve(args: argparse.Namespace) -> None:
	uvicorn.run("api:app", host=args.host, port=args.port, reload=args.reload)


def main() -> None:
	parser = argparse.ArgumentParser(prog="archviz")
	sub = parser.add_subparsers(dest="cmd", required=True)

	pa = sub.add_parser("analyze", help="Analyze a repository and print facts JSON")
	pa.add_argument("path", help="Path to repository root")
	pa.set_defaults(func=cmd_analyze)

	ps = sub.add_parser("serve", help="Run FastAPI server")
	ps.add_argument("--host", default="127.0.0.1")
	ps.add_argument("--port", type=int, default=8000)
	ps.add_argument("--reload", action="store_true")
	ps.set_defaults(func=cmd_serve)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()


