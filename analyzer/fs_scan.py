from __future__ import annotations

import os
from typing import Dict, Iterable, List, Tuple

from .model import FileInfo


EXTENSION_LANGUAGE: Dict[str, str] = {
	".py": "python",
	".ts": "typescript",
	".tsx": "typescript",
	".js": "javascript",
	".jsx": "javascript",
	".java": "java",
	".go": "go",
	".rs": "rust",
	".c": "c",
	".cpp": "cpp",
}


def detect_language(filename: str) -> str:
	_, ext = os.path.splitext(filename)
	return EXTENSION_LANGUAGE.get(ext.lower(), "unknown")


def to_module_name(root: str, file_path: str) -> str:
	rel_path = os.path.relpath(file_path, root)
	without_ext = os.path.splitext(rel_path)[0]
	parts = []
	for part in without_ext.split(os.sep):
		if part == "__init__":
			continue
		parts.append(part)
	return ".".join(parts).replace("-", "_")


def to_package_name(module_name: str) -> str:
	if "." in module_name:
		return module_name.rsplit(".", 1)[0]
	return ""


def scan_repository(root: str) -> List[FileInfo]:
	files: List[FileInfo] = []
	for dirpath, dirnames, filenames in os.walk(root):
		# Skip common ignore dirs
		dirnames[:] = [
			d for d in dirnames if d not in {".git", "node_modules", "dist", "build", "__pycache__"}
		]
		for filename in filenames:
			path = os.path.join(dirpath, filename)
			language = detect_language(filename)
			rel_path = os.path.relpath(path, root)
			module = None
			package = None
			if language == "python" and filename.endswith((".py")):
				module = to_module_name(root, path)
				package = to_package_name(module)
			files.append(
				FileInfo(
					path=path,
					rel_path=rel_path,
					language=language,
					package=package or None,
					module=module or None,
				)
			)
	return files


