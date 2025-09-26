from textwrap import dedent

from analyzer.ast_parse import parse_python_module


def test_parse_simple_module(tmp_path):
	code = dedent(
		"""
		import os
		from sys import path as sys_path

		class A(Base):
			def m(self, x, *, y=1, **kw):
				return x

		def f(a, b=2, *args, **kwargs):
			return a + b
		"""
	)
	p = tmp_path / "m.py"
	p.write_text(code)
	facts = parse_python_module("pkg.m", str(p), p.read_text())
	assert facts.module == "pkg.m"
	assert "os" in facts.imports
	assert any(c.name == "A" for c in facts.classes)
	assert any(fn.name == "f" for fn in facts.functions)


