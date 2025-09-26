from __future__ import annotations

from typing import Dict, List

from .model import ModuleFacts, RepoFacts, Summaries


def summarize_module(f: ModuleFacts) -> str:
	parts: List[str] = []
	parts.append(f"Module {f.module} at {f.path}")
	if f.classes:
		parts.append(f"  Classes: {', '.join(c.name for c in f.classes)}")
	if f.functions:
		parts.append(f"  Functions: {', '.join(fn.name for fn in f.functions)}")
	if f.imports:
		parts.append(f"  Imports: {', '.join(sorted(f.imports)[:10])}")
	return "\n".join(parts)


def summarize_repo(facts: RepoFacts) -> Summaries:
	per_module: Dict[str, str] = {}
	for m in facts.modules:
		per_module[m.module] = summarize_module(m)

	per_package: Dict[str, str] = {}
	for pkg, pkg_facts in facts.packages.items():
		mod_count = len(pkg_facts.modules)
		class_count = sum(len(m.classes) for m in pkg_facts.modules)
		func_count = sum(len(m.functions) for m in pkg_facts.modules)
		per_package[pkg] = (
			f"Package {pkg}: {mod_count} modules, {class_count} classes, {func_count} functions"
		)

	global_overview = (
		f"Repository at {facts.root}: {len(facts.files)} files, "
		f"{len([f for f in facts.files if f.language == 'python'])} python files, "
		f"{len(facts.modules)} python modules"
	)

	return Summaries(
		global_overview=global_overview,
		per_package=per_package,
		per_module=per_module,
	)


