from __future__ import annotations

import ast
from typing import List

from .model import ClassInfo, FunctionInfo, ModuleFacts


def _get_decorator_names(node: ast.AST) -> List[str]:
	decorators: List[str] = []
	for deco in getattr(node, "decorator_list", []) or []:
		if isinstance(deco, ast.Name):
			decorators.append(deco.id)
		elif isinstance(deco, ast.Attribute):
			# Collect dotted attribute like module.decorator
			parts: List[str] = []
			cursor = deco
			while isinstance(cursor, ast.Attribute):
				parts.append(cursor.attr)
				cursor = cursor.value  # type: ignore[assignment]
			if isinstance(cursor, ast.Name):
				parts.append(cursor.id)
			decorators.append(".".join(reversed(parts)))
		else:
			decorators.append(ast.unparse(deco))
	return decorators


def _format_args(args: ast.arguments) -> str:
	# Build a readable signature string
	parts: List[str] = []
	for a in args.posonlyargs:
		parts.append(a.arg)
	if args.posonlyargs:
		parts.append("/")
	for a in args.args:
		parts.append(a.arg)
	if args.vararg:
		parts.append("*" + args.vararg.arg)
	elif args.kwonlyargs:
		parts.append("*")
	for a in args.kwonlyargs:
		parts.append(a.arg)
	if args.kwarg:
		parts.append("**" + args.kwarg.arg)
	return ", ".join(parts)


def parse_python_module(module_name: str, path: str, text: str) -> ModuleFacts:
	tree = ast.parse(text, filename=path)
	imports: List[str] = []
	classes: List[ClassInfo] = []
	functions: List[FunctionInfo] = []

	for node in tree.body:
		if isinstance(node, (ast.Import, ast.ImportFrom)):
			if isinstance(node, ast.Import):
				for alias in node.names:
					imports.append(alias.name)
			elif isinstance(node, ast.ImportFrom):
				module = node.module or ""
				for alias in node.names:
					name = f"{module}.{alias.name}" if module else alias.name
					imports.append(name)
		elif isinstance(node, ast.ClassDef):
			bases = [ast.unparse(b) for b in node.bases]
			methods: List[FunctionInfo] = []
			for sub in node.body:
				if isinstance(sub, ast.FunctionDef):
					methods.append(
						FunctionInfo(
							name=sub.name,
							signature=f"({ _format_args(sub.args) })",
							decorators=_get_decorator_names(sub),
						)
					)
			classes.append(
				ClassInfo(
					name=node.name,
					bases=bases,
					decorators=_get_decorator_names(node),
					methods=methods,
				)
			)
		elif isinstance(node, ast.FunctionDef):
			functions.append(
				FunctionInfo(
					name=node.name,
					signature=f"({ _format_args(node.args) })",
					decorators=_get_decorator_names(node),
				)
			)

	return ModuleFacts(
		module=module_name,
		path=path,
		imports=sorted(set(imports)),
		classes=classes,
		functions=functions,
	)


