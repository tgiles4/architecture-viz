"""Analyzer package for extracting architectural and design facts from codebases.

Modules:
- fs_scan.py: Filesystem scanning and language detection.
- ast_parse.py: Python AST parsing to extract symbols and imports.
- model.py: Data structures for facts and dependency graphs.
- summarize.py: Deterministic textual summarization of facts.
"""

__all__ = [
	"fs_scan",
	"ast_parse",
	"model",
	"summarize",
]


