"""Smoke tests ensuring example modules import successfully."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_MODULE_PATHS = [
    REPO_ROOT / "examples" / "ui" / "ui_example.py",
    REPO_ROOT / "examples" / "game" / "main.py",
]


@pytest.mark.parametrize("module_path", EXAMPLE_MODULE_PATHS)
def test_example_module_imports(module_path: Path) -> None:
    """Each example module should load without missing API errors."""
    assert module_path.exists(), f"Missing example module: {module_path}"

    module_name = f"example_{module_path.stem}"
    spec = spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
