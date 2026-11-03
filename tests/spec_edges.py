"""Acceptance tests: YAML parsing unification (AC-4).

Verifies edges._read_yaml_docs is removed and edges.py uses yamlsafe
exclusively.
"""

from __future__ import annotations

import inspect

import pytest

from flux_topology import edges


def test_read_yaml_docs_removed():
    assert not hasattr(edges, "_read_yaml_docs"), (
        "edges._read_yaml_docs must be removed (AC-4)"
    )


def test_edges_uses_yamlsafe_read_yaml_all():
    src = inspect.getsource(edges)
    assert "read_yaml_all" in src, (
        "edges.py must use yamlsafe.read_yaml_all for YAML parsing"
    )
    assert "yaml.safe_load_all" not in src, (
        "edges.py must not fall back to raw yaml.safe_load_all"
    )


def test_edges_imports_yamlsafe_module():
    src = inspect.getsource(edges)
    assert ".yamlsafe" in src, (
        "edges.py must import from the .yamlsafe module"
    )


# --- gaps (contract silent) ------------------------------------------------

def test_yaml_read_error_handling_parity():
    """GAP-06: error-handling parity after removing _read_yaml_docs unspecified."""
    pytest.skip(
        "GAP-06: the former _read_yaml_docs read files with errors='replace' "
        "and tolerated OSError / YAMLError by returning []. yamlsafe.read_yaml_all "
        "uses path.read_text() without errors='replace' and raises on non-UTF8 "
        "bytes. The contract does not specify which tolerance the replacement "
        "must keep; a regression here silently drops edges from binary or "
        "non-UTF8 YAML files."
    )
