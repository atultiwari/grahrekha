"""D-011: core must never import the optional AGPL adapters package."""

import ast
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "src" / "grahrekha_engine"
FORBIDDEN_PREFIX = "grahrekha_adapters_agpl"


def _imported_modules(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_scanner_detects_forbidden_imports() -> None:
    sample = ast.parse("import grahrekha_adapters_agpl.swisseph\nfrom os import path")
    assert FORBIDDEN_PREFIX + ".swisseph" in _imported_modules(sample)


def test_core_never_imports_agpl_adapters() -> None:
    offenders = [
        f"{path.relative_to(CORE)} imports {name}"
        for path in CORE.rglob("*.py")
        for name in _imported_modules(ast.parse(path.read_text()))
        if name.split(".")[0] == FORBIDDEN_PREFIX
    ]
    assert offenders == [], offenders
