from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel


class FileInfo(BaseModel):
	path: str
	rel_path: str
	language: str
	package: Optional[str] = None
	module: Optional[str] = None


class FunctionInfo(BaseModel):
	name: str
	signature: str
	decorators: List[str] = []


class ClassInfo(BaseModel):
	name: str
	bases: List[str] = []
	decorators: List[str] = []
	methods: List[FunctionInfo] = []


class ModuleFacts(BaseModel):
	module: str
	path: str
	imports: List[str] = []
	classes: List[ClassInfo] = []
	functions: List[FunctionInfo] = []


class PackageFacts(BaseModel):
	package: str
	modules: List[ModuleFacts] = []


class DependencyEdge(BaseModel):
	from_module: str
	to_module: str


class RepoFacts(BaseModel):
	root: str
	files: List[FileInfo]
	modules: List[ModuleFacts]
	packages: Dict[str, PackageFacts]
	dependencies: List[DependencyEdge]


class Summaries(BaseModel):
	global_overview: str
	per_package: Dict[str, str]
	per_module: Dict[str, str]


class AnalyzeResult(BaseModel):
	facts: RepoFacts
	summaries: Summaries


